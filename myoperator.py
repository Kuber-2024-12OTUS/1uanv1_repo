import kopf
import kubernetes.client
from kubernetes.client import V1Deployment, V1ObjectMeta, V1OwnerReference
from kubernetes.client.rest import ApiException

@kopf.on.create('otus.homework', 'v1', 'mysqls')
def create_fn(spec, name, namespace, logger, **kwargs):
    image = spec.get('image')
    database = spec.get('database')
    password = spec.get('password')
    storage_size = spec.get('storage_size')

    deployment = V1Deployment(
        metadata=V1ObjectMeta(
            name=name,
            namespace=namespace,
            labels={"app": "mysql"},
        ),
        spec={
            "replicas": 1,
            "selector": {"matchLabels": {"app": "mysql"}},
            "template": {
                "metadata": {"labels": {"app": "mysql"}},
                "spec": {
                    "containers": [{
                        "name": "mysql",
                        "image": image,
                        "env": [
                            {"name": "MYSQL_DATABASE", "value": database},
                            {"name": "MYSQL_ROOT_PASSWORD", "value": password}
                        ]
                    }]
                }
            }
        }
    )

    kopf.adopt(deployment)

    api_instance = kubernetes.client.AppsV1Api()
    try:
        api_instance.create_namespaced_deployment(namespace, deployment)
        logger.info(f"Deployment создан: {name}")
    except ApiException as e:
        logger.error(f"Ошибка при создании Deployment: {e}")

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {"name": name, "namespace": namespace},
        "spec": {
            "selector": {"app": "mysql"},
            "ports": [{"port": 3306}]
        }
    }
    core_api = kubernetes.client.CoreV1Api()
    try:
        core_api.create_namespaced_service(namespace, service)
        logger.info(f"Service создан: {name}")
    except ApiException as e:
        logger.error(f"Ошибка при создании Service: {e}")

    pvc = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {"name": f"{name}-pvc", "namespace": namespace},
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {"requests": {"storage": storage_size}}
        }
    }
    try:
        core_api.create_namespaced_persistent_volume_claim(namespace, pvc)
        logger.info(f"PVC создан: {name}-pvc")
    except ApiException as e:
        logger.error(f"Ошибка при создании PVC: {e}")
