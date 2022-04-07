/*
   Copyright 2020 Docker Compose CLI authors

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

package compose

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"strings"

	"github.com/compose-spec/compose-go/types"
	"github.com/docker/cli/cli/command"
	"github.com/docker/cli/cli/config/configfile"
	"github.com/docker/cli/cli/streams"
	"github.com/docker/compose/v2/pkg/api"
	moby "github.com/docker/docker/api/types"
	"github.com/docker/docker/api/types/filters"
	"github.com/docker/docker/client"
	"github.com/pkg/errors"
	"github.com/sanathkr/go-yaml"
)

// Separator is used for naming components
var Separator = "-"

// NewComposeService create a local implementation of the compose.Service API
func NewComposeService(dockerCli command.Cli) api.Service {
	return &composeService{
		dockerCli: dockerCli,
	}
}

type composeService struct {
	dockerCli command.Cli
}

func (s *composeService) apiClient() client.APIClient {
	return s.dockerCli.Client()
}

func (s *composeService) configFile() *configfile.ConfigFile {
	return s.dockerCli.ConfigFile()
}

func (s *composeService) stdout() *streams.Out {
	return s.dockerCli.Out()
}

func (s *composeService) stdin() *streams.In {
	return s.dockerCli.In()
}

func (s *composeService) stderr() io.Writer {
	return s.dockerCli.Err()
}

func getCanonicalContainerName(c moby.Container) string {
	if len(c.Names) == 0 {
		// corner case, sometime happens on removal. return short ID as a safeguard value
		return c.ID[:12]
	}
	// Names return container canonical name /foo  + link aliases /linked_by/foo
	for _, name := range c.Names {
		if strings.LastIndex(name, "/") == 0 {
			return name[1:]
		}
	}
	return c.Names[0][1:]
}

func getContainerNameWithoutProject(c moby.Container) string {
	name := getCanonicalContainerName(c)
	project := c.Labels[api.ProjectLabel]
	prefix := fmt.Sprintf("%s_%s_", project, c.Labels[api.ServiceLabel])
	if strings.HasPrefix(name, prefix) {
		return name[len(project)+1:]
	}
	return name
}

func (s *composeService) Convert(ctx context.Context, project *types.Project, options api.ConvertOptions) ([]byte, error) {
	switch options.Format {
	case "json":
		marshal, err := json.MarshalIndent(project, "", "  ")
		if err != nil {
			return nil, err
		}
		return escapeDollarSign(marshal), nil
	case "yaml":
		marshal, err := yaml.Marshal(project)
		if err != nil {
			return nil, err
		}
		return escapeDollarSign(marshal), nil
	default:
		return nil, fmt.Errorf("unsupported format %q", options)
	}
}

func escapeDollarSign(marshal []byte) []byte {
	dollar := []byte{'$'}
	escDollar := []byte{'$', '$'}
	return bytes.ReplaceAll(marshal, dollar, escDollar)
}

// projectFromName builds a types.Project based on actual resources with compose labels set
func (s *composeService) projectFromName(containers Containers, projectName string, services ...string) (*types.Project, error) {
	project := &types.Project{
		Name: projectName,
	}
	if len(containers) == 0 {
		return project, errors.Wrap(api.ErrNotFound, fmt.Sprintf("no container found for project %q", projectName))
	}
	set := map[string]*types.ServiceConfig{}
	for _, c := range containers {
		serviceLabel := c.Labels[api.ServiceLabel]
		_, ok := set[serviceLabel]
		if !ok {
			set[serviceLabel] = &types.ServiceConfig{
				Name:   serviceLabel,
				Image:  c.Image,
				Labels: c.Labels,
			}
		}
		set[serviceLabel].Scale++
	}
	for _, service := range set {
		dependencies := service.Labels[api.DependenciesLabel]
		if len(dependencies) > 0 {
			service.DependsOn = types.DependsOnConfig{}
			for _, dc := range strings.Split(dependencies, ",") {
				dcArr := strings.Split(dc, ":")
				condition := ServiceConditionRunningOrHealthy
				dependency := dcArr[0]

				// backward compatibility
				if len(dcArr) > 1 {
					condition = dcArr[1]
				}
				service.DependsOn[dependency] = types.ServiceDependency{Condition: condition}
			}
		}

		links := service.Labels[api.LinksLabel]
		if len(links) > 0 {
			for _, link := range strings.Split(links, ",") {
				l := strings.Split(link, ":")[0]
				service.Links = append(service.Links, l)
			}
		}
		project.Services = append(project.Services, *service)
	}
SERVICES:
	for _, qs := range services {
		for _, es := range project.Services {
			if es.Name == qs {
				continue SERVICES
			}
		}
		return project, errors.Wrapf(api.ErrNotFound, "no such service: %q", qs)
	}
	err := project.ForServices(services)
	if err != nil {
		return project, err
	}

	return project, nil
}

// actualState list resources labelled by projectName to rebuild compose project model
func (s *composeService) actualState(ctx context.Context, projectName string, services []string) (Containers, *types.Project, error) {
	var containers Containers
	// don't filter containers by options.Services so projectFromName can rebuild project with all existing resources
	containers, err := s.getContainers(ctx, projectName, oneOffInclude, true)
	if err != nil {
		return nil, nil, err
	}

	project, err := s.projectFromName(containers, projectName, services...)
	if err != nil && !api.IsNotFoundError(err) {
		return nil, nil, err
	}

	if len(services) > 0 {
		containers = containers.filter(isService(services...))
	}
	return containers, project, nil
}

func (s *composeService) actualVolumes(ctx context.Context, projectName string) (types.Volumes, error) {
	volumes, err := s.apiClient().VolumeList(ctx, filters.NewArgs(projectFilter(projectName)))
	if err != nil {
		return nil, err
	}

	actual := types.Volumes{}
	for _, vol := range volumes.Volumes {
		actual[vol.Labels[api.VolumeLabel]] = types.VolumeConfig{
			Name:   vol.Name,
			Driver: vol.Driver,
			Labels: vol.Labels,
		}
	}
	return actual, nil
}

func (s *composeService) actualNetworks(ctx context.Context, projectName string) (types.Networks, error) {
	networks, err := s.apiClient().NetworkList(ctx, moby.NetworkListOptions{
		Filters: filters.NewArgs(projectFilter(projectName)),
	})
	if err != nil {
		return nil, err
	}

	actual := types.Networks{}
	for _, net := range networks {
		actual[net.Labels[api.NetworkLabel]] = types.NetworkConfig{
			Name:   net.Name,
			Driver: net.Driver,
			Labels: net.Labels,
		}
	}
	return actual, nil
}
