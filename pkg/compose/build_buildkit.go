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
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/compose-spec/compose-go/types"
	"github.com/docker/buildx/build"
	"github.com/docker/buildx/driver"
	xprogress "github.com/docker/buildx/util/progress"
)

func (s *composeService) doBuildBuildkit(ctx context.Context, project *types.Project, opts map[string]build.Options, mode string) (map[string]string, error) {
	const drivername = "default"
	d, err := driver.GetDriver(ctx, drivername, nil, s.apiClient, s.configFile, nil, nil, "", nil, nil, project.WorkingDir)
	if err != nil {
		return nil, err
	}
	driverInfo := []build.DriverInfo{
		{
			Name:   drivername,
			Driver: d,
		},
	}

	// Progress needs its own context that lives longer than the
	// build one otherwise it won't read all the messages from
	// build and will lock
	progressCtx, cancel := context.WithCancel(context.Background())
	defer cancel()
	w := xprogress.NewPrinter(progressCtx, os.Stdout, mode)

	var servicesName []string
	for name := range opts {
		servicesName = append(servicesName, name[strings.LastIndex(name, "_")+1:])
	}
	fmt.Printf("building %s\n", strings.Join(servicesName, ", "))

	// We rely on buildx "docker" builder integrated in docker engine, so don't need a DockerAPI here
	response, err := build.Build(ctx, driverInfo, opts, nil, nil, w)
	errW := w.Wait()
	if err == nil {
		err = errW
	}
	if err != nil {
		return nil, WrapCategorisedComposeError(err, BuildFailure)
	}

	imagesBuilt := map[string]string{}
	for name, img := range response {
		if img == nil || len(img.ExporterResponse) == 0 {
			continue
		}
		digest, ok := img.ExporterResponse["containerimage.digest"]
		if !ok {
			continue
		}
		imagesBuilt[name] = digest
	}
	if len(servicesName) > 1 {
		fmt.Printf("WARNING: Images for services %s were built because they did not already exist. "+
			"To rebuild those images you must use `docker compose build` or `docker compose up --build`.\n",
			strings.Join(servicesName, ", "))
	} else {
		fmt.Printf("WARNING: Image for service %s was built because it did not already exist. "+
			"To rebuild this image you must use `docker compose build` or `docker compose up --build`.\n",
			servicesName[0])
	}

	return imagesBuilt, err
}
