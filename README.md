# Intermediate Kubernetes

This presentation assumes the audience has a basic understanding of what is Kubernetes. The intent is to show how a Developer might use Kubernetes
to build and deploy his/her code. We also want to show how using a managed services like AKS makes Kubernetes a technology that is 
actually easy to use. I would submit it's simpler to create and use an AKS cluster, than it is to build and deploy Virtual machines. 

This presentation deliberately does not use [Terraform](https://www.terraform.io/) because that is a tool used by SREs to managing infrastructure at scale. It is not a pre-requisite to using/learning Kubernetes.

This presentation does not discuss advanced docker build techniques ([Docker BuildKit](https://docs.docker.com/develop/develop-images/build_enhancements/), [Kaniko](https://github.com/GoogleContainerTools/kaniko), [Buildpacks](https://buildpacks.io/)), nor does it delve into tooling that would improve the developer experience ([VSCode support](https://code.visualstudio.com/docs/azure/kubernetes), [Skaffold](https://skaffold.dev/), [Devspace](https://devspace.sh/)). 

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

    make build

Which will run the following docker commands

    docker build -t scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528 .
    docker push scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528

The docker image name format is as follows:

    <registry>/<project>/<name>:<tag>

# Part 4: Deploy container(s) to AKS using helm

Run the demo

    make build deploy

which runs the following commands to build a new docker image and then deploy it using helm

    docker build -t scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528 .
    docker push scoil1.azurecr.io/myspotontheweb/scoil:v1.0-2-ga36e528

    helm upgrade scoil chart --install \
        --set image.repository=scoil1.azurecr.io/myspotontheweb/scoil \
        --set image.tag=v1.0-2-ga36e528 \
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

    NAME                         READY   STATUS    RESTARTS   AGE
    pod/scoil-64dc8fc7b8-tpbbf   1/1     Running   0          4m5s
        
    NAME            TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
    service/scoil   ClusterIP   10.0.227.184   <none>        8080/TCP   4m5s
        
    NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/scoil   1/1     1            1           4m6s
        
    NAME                               DESIRED   CURRENT   READY   AGE
    replicaset.apps/scoil-64dc8fc7b8   1         1         1       4m6s
        
    NAME                                        REFERENCE          TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
    horizontalpodautoscaler.autoscaling/scoil   Deployment/scoil   <unknown>/50%   1         100       1          4m6s

NOTES:

* A single pod is running
* The "service" declaration acts as a DNS loadbalancer within the k8s cluster
* The deployment object is the controller that manages the pods
* Each new release will create a replicaset. This is an internal detail to how Deployments work
* There is also a pod autoscaler, which is configured to scale when the average pod CPU utilization exceeds 50%


## Have a look at the output

Start a secure tunnel

    kubectl port-forward service/scoil 8080:8080

and access the website on this link

* http://localhost:8080

## Manually scale up the application

Run 10 pods

    kubectl scale deployment.apps/scoil --replicas=10

What them being created

    $ kubectl get all
    NAME                         READY   STATUS              RESTARTS   AGE
    pod/scoil-64dc8fc7b8-7pbk7   1/1     Running             0          6s
    pod/scoil-64dc8fc7b8-bbmmd   1/1     Running             0          6s
    pod/scoil-64dc8fc7b8-bd8qf   0/1     ContainerCreating   0          6s
    pod/scoil-64dc8fc7b8-cg6td   1/1     Running             0          6s
    pod/scoil-64dc8fc7b8-jm8k4   0/1     ContainerCreating   0          6s
    pod/scoil-64dc8fc7b8-kqvwd   0/1     ContainerCreating   0          6s
    pod/scoil-64dc8fc7b8-kzvrw   0/1     ContainerCreating   0          6s
    pod/scoil-64dc8fc7b8-nnpgb   0/1     ContainerCreating   0          6s
    pod/scoil-64dc8fc7b8-tpbbf   1/1     Running             0          11m
    pod/scoil-64dc8fc7b8-zq46p   1/1     Running             0          6s
    
    NAME            TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)    AGE
    service/scoil   ClusterIP   10.0.227.184   <none>        8080/TCP   11m
    
    NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
    deployment.apps/scoil   5/10    10           5           11m
    
    NAME                               DESIRED   CURRENT   READY   AGE
    replicaset.apps/scoil-64dc8fc7b8   10        10        5       11m
    
    NAME                                        REFERENCE          TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
    horizontalpodautoscaler.autoscaling/scoil   Deployment/scoil   <unknown>/50%   1         100       10         11m

And you can see where the pods are running

    $ kubectl get pods -owide
    NAME                     READY   STATUS    RESTARTS   AGE     IP            NODE                                NOMINATED NODE   READINESS GATES
    scoil-64dc8fc7b8-7pbk7   1/1     Running   0          4m56s   10.244.1.6    aks-nodepool1-27971391-vmss000001   <none>           <none>
    scoil-64dc8fc7b8-bbmmd   1/1     Running   0          4m56s   10.244.1.8    aks-nodepool1-27971391-vmss000001   <none>           <none>
    scoil-64dc8fc7b8-bd8qf   1/1     Running   0          4m56s   10.244.0.9    aks-nodepool1-27971391-vmss000000   <none>           <none>
    scoil-64dc8fc7b8-cg6td   1/1     Running   0          4m56s   10.244.1.7    aks-nodepool1-27971391-vmss000001   <none>           <none>
    scoil-64dc8fc7b8-jm8k4   1/1     Running   0          4m56s   10.244.0.10   aks-nodepool1-27971391-vmss000000   <none>           <none>
    scoil-64dc8fc7b8-kqvwd   1/1     Running   0          4m56s   10.244.0.12   aks-nodepool1-27971391-vmss000000   <none>           <none>
    scoil-64dc8fc7b8-kzvrw   1/1     Running   0          4m56s   10.244.0.8    aks-nodepool1-27971391-vmss000000   <none>           <none>
    scoil-64dc8fc7b8-nnpgb   1/1     Running   0          4m56s   10.244.0.11   aks-nodepool1-27971391-vmss000000   <none>           <none>
    scoil-64dc8fc7b8-tpbbf   1/1     Running   0          16m     10.244.1.4    aks-nodepool1-27971391-vmss000001   <none>           <none>
    scoil-64dc8fc7b8-zq46p   1/1     Running   0          4m56s   10.244.1.5    aks-nodepool1-27971391-vmss000001   <none>           <none>

## Restart the pods

The best way to restart pods is to tell the Deployment object to perform a rolling restart of each pod as follows:

    kubectl rollout restart deployment/scoil

This will play "whack-a-mole" slowing terminating old pods and gradually creating new ones. This strategy means there is always pod
available to serve traffic. 

## Simulate load scaling

Reduce the number of pods back to 1

    kubectl scale deployment.apps/scoil --replicas=1

Start a pod within the cluster

    kubectl run -i --tty load-generator --rm --image=busybox:1.28 --restart=Never -- /bin/sh -c "while sleep 0.01; do wget -q -O- http://scoil:8080; done"

> **_NOTE:_**  This demo is not working yet. Need to revise the application to make it more CPU intensive so that we can push it to 50% utilization

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

# Part 5: Cleanup

Run the demo

    make clean

This will run the following command that will delete all the provisioned infrastructure

    az group delete --name scoil-1 --yes --no-wait

