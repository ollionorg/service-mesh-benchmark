# Orchestrator

This chart is used to deploy the orchestrator application which can be used to deploy benchmarking clusters, run benchmarks on them, etc. This chart can be deployed on any Lokomotive cluster regardless or the region, the underlying architecture or cloud provider.

## General Usage
### Install

Run the following command to install the helm chart:

```bash
helm install \
    --values=values-real.yaml \
    --set-file runScript=run.sh \
    --set-file sshKey.public=$HOME/.ssh/id_rsa.pub \
    --set-file sshKey.private=$HOME/.ssh/id_rsa \
    --create-namespace \
    --namespace orchestrator \
    orchestrator .
```

Copy the the [values.yaml](values.yaml) file and make changes as necessary and rename it to `values-real.yaml`.

Update the path of the SSH keys as required.

### Upgrade

```bash
helm upgrade \
    --values=values-real.yaml \
    --set-file runScript=run.sh \
    --set-file sshKey.public=$HOME/.ssh/id_rsa.pub \
    --set-file sshKey.private=$HOME/.ssh/id_rsa \
    --namespace orchestrator \
    orchestrator .
```

### Delete

```
helm uninstall orchestrator
kubectl delete ns orchestrator
```

## Writing a script

- Write a script that deploys the cluster and installs the components on Lokomotive cluster.
- Followed by cluster and component installation design your script to deploy target benchmarking applications.
- Start off using the scaffold provided in [run.sh](cluster-install-configs/run.sh).
- Take inspiration from the existing [run-smi-benchmark.sh](cluster-install-configs/run-smi-benchmark.sh)

## Clean up benchmarking clusters

Exec into the debug pod:

```bash
kubectl -n orchestrator exec -it $(kubectl -n orchestrator get pod -l app=debug-jobs -o name) bash
```

Run the clean up script:

```bash
bash /scripts/cleanup.sh
```

## Debug failed cluster

Exec into the debug pod:

```bash
kubectl -n orchestrator exec -it $(kubectl -n orchestrator get pod -l app=debug-jobs -o name) bash
```

You can find all the cluster assets and related config in the `/clusters` directory. You can use these assets to interact with the cluster.
