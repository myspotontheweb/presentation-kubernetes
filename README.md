# presentation-kubernetes

Intermediate presentation of Kubernetes

# Part 1: Provision an AKS cluster

Run the demo

    make provision

which will run the following commands that will provision an Azure ACR registry and an Azure AKS cluster

    az account set --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    az group create --name scoil-1 --location eastus
    az acr create --resource-group scoil-1 --name scoil1 --sku Basic
    az aks create --resource-group scoil-1 --name scoil-1 --node-count 2 --attach-acr scoil1

The last command will take approx 5 mins to run so be patient

# Part 2: Build and push a Docker container image

Run the demo

    make build

Which will run the following docker commands

    docker build -t scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528 .
    docker push scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528

The docker image name format is as follows:

    <registry>/<project>/<name>:<tag>

# Part 3: Deploy container image to AKS using helm

Run the demo

    make build deploy

which runs the following commands to build a new docker image and then deploy it using helm

    docker build -t scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528 .
    docker push scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528
    helm upgrade scoil chart --set image.repository=scoil1.azurecr.io/myspotontheweb/scoil --set image.tag=v1.0-2-ga36e528 --namespace mark --create-namespace

NOTES:

* Helm is a tool for generating the Kubernetes API YAML
* The details of the newly built image is passed as parameters
* The target namespace is also specified

## Rendered YAML

If you want to look at the generated YAML

    make render

Sample:

    ---
    # Source: scoil/templates/serviceaccount.yaml
    apiVersion: v1
    kind: ServiceAccount
    metadata:
      name: scoil
      labels:
        helm.sh/chart: scoil-0.1.0
        app.kubernetes.io/name: scoil
        app.kubernetes.io/instance: scoil
        app.kubernetes.io/version: "1.16.0"
        app.kubernetes.io/managed-by: Helm
    ---
    # Source: scoil/templates/service.yaml
    apiVersion: v1
    kind: Service
    metadata:
      name: scoil
      labels:
        helm.sh/chart: scoil-0.1.0
        app.kubernetes.io/name: scoil
        app.kubernetes.io/instance: scoil
        app.kubernetes.io/version: "1.16.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      type: ClusterIP
      ports:
        - port: 8080
          targetPort: http
          protocol: TCP
          name: http
      selector:
        app.kubernetes.io/name: scoil
        app.kubernetes.io/instance: scoil
    ---
    # Source: scoil/templates/deployment.yaml
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: scoil
      labels:
        helm.sh/chart: scoil-0.1.0
        app.kubernetes.io/name: scoil
        app.kubernetes.io/instance: scoil
        app.kubernetes.io/version: "1.16.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      selector:
        matchLabels:
          app.kubernetes.io/name: scoil
          app.kubernetes.io/instance: scoil
      template:
        metadata:
          labels:
            app.kubernetes.io/name: scoil
            app.kubernetes.io/instance: scoil
        spec:
          serviceAccountName: scoil
          securityContext:
            {}
          containers:
            - name: scoil
              securityContext:
                {}
              image: "scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528"
              imagePullPolicy: IfNotPresent
              ports:
                - name: http
                  containerPort: 8080
                  protocol: TCP
              livenessProbe:
                httpGet:
                  path: /
                  port: http
              readinessProbe:
                httpGet:
                  path: /
                  port: http
              resources:
                {}
    ---
    # Source: scoil/templates/hpa.yaml
    apiVersion: autoscaling/v2beta1
    kind: HorizontalPodAutoscaler
    metadata:
      name: scoil
      labels:
        helm.sh/chart: scoil-0.1.0
        app.kubernetes.io/name: scoil
        app.kubernetes.io/instance: scoil
        app.kubernetes.io/version: "1.16.0"
        app.kubernetes.io/managed-by: Helm
    spec:
      scaleTargetRef:
        apiVersion: apps/v1
        kind: Deployment
        name: scoil
      minReplicas: 1
      maxReplicas: 100
      metrics:
        - type: Resource
          resource:
            name: cpu
            targetAverageUtilization: 50
