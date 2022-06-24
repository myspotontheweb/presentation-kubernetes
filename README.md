# Intermediate Kubernetes

This presentation assumes the audience has a basic understanding of what is Kubernetes. The intent is to show how a Developer might use Kubernetes
to build and deploy his/her code. We also want to show how using a managed services like AKS makes Kubernetes a technology that is 
actually easy to use.

This presentation deliberately does not use [Terraform](https://www.terraform.io/) because that is a tool used by SREs to managing infrastructure at scale. It is not a pre-requisite to using/learning Kubernetes.

This presentation does not discuss alternative docker build techniques ([Podman](https://podman.io/), [Kaniko](https://github.com/GoogleContainerTools/kaniko), [Buildpacks](https://buildpacks.io/)), nor does it delve into tooling that would improve the developer experience ([VSCode support](https://code.visualstudio.com/docs/azure/kubernetes), [Skaffold](https://skaffold.dev/), [Devspace](https://devspace.sh/)). 

In this demo we'll

1. Provision an Azure AKS kubernetes cluster and ACR docker registry
1. Show how to access the cluster and registry
1. Build and push a Docker container image
1. Deploy a container to AKS using helm. Demonstrate additional capabilities such as scaling
1. Purge provisioned infrastructure

## Recommended reading

* [Azure Kubernetes Service (AKS)](https://docs.microsoft.com/en-us/azure/aks/)
* [Kubernetes Documentation](https://kubernetes.io/docs)
* [Helm](https://helm.sh/docs/)

## Required software

* Azure subscription
* Windows WSL2 using Ubuntu 
* Docker CE
* Azure cli
* kubectl cli
* helm cli

## How to get started?

Clone this repo

    git clone https://github.com/myspotontheweb/presentation-kubernetes.git
    cd presentation-kubernetes/demo


# Part 1: Provision an AKS cluster

Run the demo

    make provision

which will run the following commands that will provision an Azure ACR registry and an Azure AKS cluster

    az account set --subscription xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    az group create --name scoil-1 --location eastus
    az acr create --resource-group scoil-1 --name scoil1 --sku Basic
    az aks create --resource-group scoil-1 --name scoil-1 --node-count 2 --attach-acr scoil1

The last command will take approx 5 mins to run so be patient

# Part 2: Login to the cluster and registry

Run the demo

    make creds

which will run the following commands

    az aks get-credentials --resource-group scoil-1 --name scoil-1
    az acr login --name scoil1.azurecr.io

NOTES:

* The first command will populate the ~/.kube/config file with connection details for the cluster
* The second command simulates a "docker login" so that images can be pushed to the ACR registry

Make sure docker is running

    sudo service docker start

# Part 3: Build and push a Docker container image

Run the demo

    make build-setup build

Which will run the following docker commands:

    docker buildx create --name scoil-builder --driver kubernetes --driver-opt replicas=1,namespace=builders --use
    kubectl create ns builders
    docker buildx build --tag  scoil1.azurecr.io/myspotontheweb/scoil1:v1.0-27-gb98678e --push .

Notes:

* Using the [Docker Buildx plugin](https://docs.docker.com/buildx/working-with-buildx/), which leverages the more powerful [Docker Buildkit engine](https://docs.docker.com/develop/develop-images/build_enhancements/).
* The first command configures an optional remote builder that runs on the Kubernetes cluster. This reduces the workload on the local laptop
* A remote build can work-around problems where a VPN product (like ZScaler) messes with SSL certs from remote repositories

The docker image name format is as follows:

    <registry>/<project>/<name>:<tag>

# Part 4: Deploy container(s) to AKS using helm

Run the demo

    make build deploy

which runs the following commands to build a new docker image and then deploy it using helm

    docker buildx build --tag  scoil1.azurecr.io/myspotontheweb/scoil1:v1.0-27-gb98678e --push .
    
    helm upgrade scoil chart --install \
       --set image.repository=scoil1.azurecr.io/myspotontheweb/scoil1 \
       --set image.tag=v1.0-27-gb98678e \
       --namespace mark \
       --create-namespace

NOTES:

* Helm is a tool for generating the Kubernetes API YAML
* The details of the newly built image is passed as "set" parameters. The image tag changes with each code commit
* The target namespace is also specified

## Check running pods

Set the namespace to match helm deployment

    kubectl config set-context --current --namespace=mark

Check what's running

    kubectl get all

Sample output

    $ kubectl get all
    NAME                         READY   STATUS    RESTARTS   AGE
    pod/scoil-7cc75f8978-52fcr   1/1     Running   0          5m19s
    pod/scoil-7cc75f8978-5qhhr   1/1     Running   0          5m19s
    
    NAME            TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
    service/scoil   ClusterIP   10.0.94.193   <none>        8080/TCP   45m
    
    NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/scoil   2/2     2            2           45m
    
    NAME                               DESIRED   CURRENT   READY   AGE
    replicaset.apps/scoil-86d6768864   2         2         2       45m

    NAME                                        REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
    horizontalpodautoscaler.autoscaling/scoil   Deployment/scoil   1%/20%    2         100       2          5m50s

NOTES:

* A single pod is running
* The "service" declaration acts as a DNS loadbalancer within the k8s cluster
* The deployment object is the controller that manages the pods
* Each new release will create a replicaset. This is an internal detail to how Deployments work
* There is also a pod autoscaler, which is configured to scale when the average pod CPU utilization exceeds 20%

## Have a look at the output

Start a secure tunnel

    kubectl port-forward service/scoil 8080:8080

and access the website on this link

* http://localhost:8080

## Restart the pods

The best way to restart pods is to tell the Deployment object to perform a rolling restart of each pod as follows:

    kubectl rollout restart deployment/scoil

This will play "whack-a-mole" slowing terminating old pods and gradually creating new ones. This strategy means there is always pod
available to serve traffic. 

## Simulate load scaling

Start a pod within the cluster that will generate lots of requests

    kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://scoil:8080/stress; done"

Wait for several minutes and you'll observe the pod autoscaler launching additional pods, when the CPU utilization exceeds the desired 20% target:

    $ kubectl get pods,hpa
    NAME                         READY   STATUS    RESTARTS   AGE
    pod/load-generator           1/1     Running   0          5m36s
    pod/scoil-7cc75f8978-57rvk   1/1     Running   0          8m26s
    pod/scoil-7cc75f8978-7gqz5   1/1     Running   0          11s
    pod/scoil-7cc75f8978-frfxh   1/1     Running   0          8m37s
    pod/scoil-7cc75f8978-zmgds   1/1     Running   0          11s
    
    NAME                                        REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
    horizontalpodautoscaler.autoscaling/scoil   Deployment/scoil   52%/20%   2         100       2          26s

Kill the load generator

    kubectl delete pod/load-generator 

and **eventually** the number of pods will reduce the minimum two.

    $ kubectl get pods,hpa
    NAME                         READY   STATUS    RESTARTS   AGE
    pod/scoil-7cc75f8978-frfxh   1/1     Running   0          19m
    pod/scoil-7cc75f8978-zmgds   1/1     Running   0          11m
    
    NAME                                        REFERENCE          TARGETS   MINPODS   MAXPODS   REPLICAS   AGE
    horizontalpodautoscaler.autoscaling/scoil   Deployment/scoil   1%/20%    2         100       2          11m

## Helm chart structure

The Helm homepage contains a [detailed description](https://helm.sh/docs/topics/charts/#the-chart-file-structure) of the Helm chart format

    $ tree demo/chart
    demo/chart
    ├── Chart.yaml
    ├── charts
    ├── templates
    │   ├── NOTES.txt
    │   ├── _helpers.tpl
    │   ├── deployment.yaml
    │   ├── hpa.yaml
    │   ├── ingress.yaml
    │   ├── service.yaml
    │   └── serviceaccount.yaml
    └── values.yaml

I didn't write this helm chart from scratch. It's easy to generate one as follows:

    helm create scoil

In practice users will spend their time tweaking existing charts. There are advanced usercases where 
[libray helm charts](https://helm.sh/docs/topics/library_charts/) can be used to standardize helm chart usage across an organisation.

## Rendered YAML

Unlike tools like [Docker Compose](https://docs.docker.com/compose/), the Kubernetes YAML was never designed for humans to read and edit directly.
Instead each YAML document represents a Kubernetes API call, this explains its apparent complexity.
While there are some kubectl commands that will generate Kubernetes objects ("kubectl run", "kubectl expose", etc) generally we use other tools
to talk to Kubernetes using its API. In this demo we used [Helm](https://helm.sh/)

If you want to look at the generated YAML

    make render

Sample:

    helm template scoil chart --set image.repository=scoil1.azurecr.io/myspotontheweb/scoil1 --set image.tag=v1.0-33-g3566061
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
              image: "scoil1.azurecr.io/myspotontheweb/scoil1:v1.0-33-g3566061"
              imagePullPolicy: Always
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
                limits:
                  cpu: 100m
                  memory: 128Mi
                requests:
                  cpu: 100m
                  memory: 128Mi
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
      minReplicas: 2
      maxReplicas: 100
      metrics:
        - type: Resource
          resource:
            name: cpu
            targetAverageUtilization: 20

# Part 5: Cleanup

Run the demo

    make purge

This will run the following command that will delete all the provisioned infrastructure

    az group delete --name scoil-1 --yes --no-wait

