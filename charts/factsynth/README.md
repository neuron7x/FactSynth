# FactSynth Helm Chart

## Ingress Options

The chart exposes `.Values.ingress.annotations` for custom [NGINX Ingress](https://kubernetes.github.io/ingress-nginx/user-guide/nginx-configuration/annotations/) settings.

### HTTPS Redirect

Enable automatic redirects from HTTP to HTTPS by adding this annotation:

```yaml
ingress:
  annotations:
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
```

### Request Body Size

Limit the maximum upload size processed by NGINX:

```yaml
ingress:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: 1m
```

Adjust the `1m` value as required.

## NetworkPolicy

Customize Kubernetes NetworkPolicy ingress rules through `.Values.networkPolicy.ingress`.
Each entry supports `podSelector`, `namespaceSelector`, or `ipBlock` sources and
optionally overrides the target port.

Example:

```yaml
networkPolicy:
  enabled: true
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
      ports:
        - port: 8000
    - from:
        - ipBlock:
            cidr: 10.0.0.0/24
      ports:
        - port: 8000
```
