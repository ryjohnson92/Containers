
# Containers Module (Python)

Useful tools for building python based applications in Docker.


## Environment Variables & Setup

To run this project, you will need to add the following variables in your environment.

`HEALTHCHECK_PORT` - int - Used to determine which port to serve healthchecks from. Defaults to 5050

#### Setting up healthchecks in your DockerFile
Since docker requires an executable file or entry command to initiate healthchecks, you'll need to add this. See below for and example healthcheck executable and assocaited dockerfile snippet.

```python
  #!/usr/bin/env python3.11
  import sys
  from Containers.health import Docker
  ### This is a wrapper, entry point for DOCKER health checks
  ### It is assumed that your app is run using 
  ### Containers.health.Docker as a base class
  sys.exit(Docker.read_healthchecks())
```

```yaml
  FROM ubuntu:20.04
  HEALTHCHECK --interval=30s --timeout=3s --retries=3 CMD [ "healthcheck" ]
  ENV HEALTHCHECK_PORT=5050
  COPY ./healthcheck /usr/local/bin
  RUN chmod +x /usr/local/bin/healthcheck
```
## Usage

#### Docker Health check wrapper
The docker health check wrapper can be used in conjunction with your entrypoint by extending the Docker class. Healthchecks can we written as subclasses of the main app class and your entrypoint can be injected via the "entrypoint" function. 

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

| Parameter | Type     | Description                |
| :-------- | :------- | :------------------------- |
| `api_key` | `string` | **Required**. Your API key |


