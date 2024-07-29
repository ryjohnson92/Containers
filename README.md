
# Containers Module (Python)

Useful tools for building python-based applications in Docker.

## Usage

### Docker Health check wrapper
The docker health check wrapper can be used in conjunction with your entrypoint by extending the Docker class. Healthchecks can be written as subclasses of the main app class and your entrypoint can be injected via the "entrypoint" function. 

#### Setting up health checks in your DockerFile
Since Docker requires an executable file or entry command to initiate healthchecks, you'll need accommodate this. See below for and example healthcheck executable and assocaited dockerfile snippet.
#### * Optional Environment setup
Additional environment variables can be set as follows

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| HEALTHCHECK_PORT | int | Used to determine which port to serve healthchecks from. Defaults to 5050 |
| BUILD_VERSION | str | build version |

#### Healthcheck Executable (Docker)
```python
  #!/usr/bin/env python3.11
  import sys
  from Containers.health import Docker
  ### This is a wrapper, entry point for DOCKER health checks
  ### It is assumed that your app is run using 
  ### Containers.health.Docker as a base class
  sys.exit(Docker.read_healthchecks())
```
#### Dockerfile (Docker)
```yaml
  FROM ubuntu:20.04
  HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD [ "healthcheck" ]
#   HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD [ "python3.11","./healthcheck.py" ] Optional usage
  ENV HEALTHCHECK_PORT=5050
  COPY ./healthcheck /usr/local/bin ## If using alternate usage, this is not required
  RUN chmod +x /usr/local/bin/healthcheck ## ""
  ENTRYPOINT ['python3.11','./myapp.py']
```
#### Example app (myapp.py)
```python
  import time
  from Containers.health import Docker

  class myapp(Docker):
      class MyCustomCheck(Docker.health_check):
          def check(self):
              return True
          pass
      class MyCustomCheck2(Docker.health_check):
          def check(self):
              return True
          pass
      class youreWrong(Docker.health_check):
          ### This check fails to load due to incorrect naming convention
          def acheck(self):
              return False
          pass
      def entrypoint(self):
          self.log.info('Starting application!')
          ### DO some stuff
          time.sleep(120)
          pass

      pass

  if __name__ == '__main__':
      myapp()
```

## API Reference

#### Get Health_checks


```http
  GET /health_check.json
```

```json
  {
    "name": "myapp",
    "services": {
      "MyCustomCheck": {
        "name": "MyCustomCheck",
        "status": "green"
      },
      "MyCustomCheck2": {
        "name": "MyCustomCheck2",
        "status": "green"
      }
    },
    "metadata": {
      "build": "unknown"
    }
  }
```


