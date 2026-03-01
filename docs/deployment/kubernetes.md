# Kubernetes Deployment Guide

This guide walks through deploying vibe-rag on Kubernetes with a PostgreSQL+pgvector
StatefulSet and a horizontally-scalable application Deployment.

---

## Prerequisites

- `kubectl` configured for your target cluster
- Container registry accessible from the cluster (e.g. Docker Hub, GCR, ECR)
- Persistent storage class available for the database PVC

---

## 1. Namespace

Keep all vibe-rag resources in a dedicated namespace:

```bash
kubectl create namespace vibe-rag
```

All `kubectl` commands below assume `--namespace vibe-rag` or use the alias:

```bash
alias k="kubectl -n vibe-rag"
```

---

## 2. Secrets

Store sensitive credentials as Kubernetes Secrets. Never commit these values to
source control.

```bash
# Gemini API key
kubectl create secret generic vibe-rag-api \
  --namespace vibe-rag \
  --from-literal=GOOGLE_API_KEY="your-gemini-api-key"

# PostgreSQL password
kubectl create secret generic vibe-rag-postgres \
  --namespace vibe-rag \
  --from-literal=POSTGRES_PASSWORD="choose-a-strong-password"
```

---

## 3. PostgreSQL StatefulSet

```yaml
# postgres-statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: vibe-rag
spec:
  serviceName: postgres-headless
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: pgvector/pgvector:pg16
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              value: vibe
            - name: POSTGRES_DB
              value: vibe_rag
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: vibe-rag-postgres
                  key: POSTGRES_PASSWORD
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          readinessProbe:
            exec:
              command: ["pg_isready", "-U", "vibe", "-d", "vibe_rag"]
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            exec:
              command: ["pg_isready", "-U", "vibe", "-d", "vibe_rag"]
            initialDelaySeconds: 30
            periodSeconds: 30
          resources:
            requests:
              cpu: "500m"
              memory: "512Mi"
            limits:
              cpu: "2"
              memory: "2Gi"
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 20Gi
```

Apply:

```bash
kubectl apply -f postgres-statefulset.yaml
```

---

## 4. Headless Service for StatefulSet

A headless Service gives the StatefulSet a stable DNS name
(`postgres-headless.vibe-rag.svc.cluster.local`) used by the application.

```yaml
# postgres-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: vibe-rag
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
    - port: 5432
      targetPort: 5432
```

Apply:

```bash
kubectl apply -f postgres-service.yaml
```

The full connection string for the application becomes:

```
postgresql://vibe:<POSTGRES_PASSWORD>@postgres-headless.vibe-rag.svc.cluster.local:5432/vibe_rag
```

---

## 5. ConfigMap

Store non-sensitive application configuration in a ConfigMap:

```yaml
# app-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vibe-rag-config
  namespace: vibe-rag
data:
  COLLECTION_NAME: "documents"
  CHUNK_SIZE: "512"
  TOP_K: "5"
```

Apply:

```bash
kubectl apply -f app-configmap.yaml
```

---

## 6. Application Deployment

```yaml
# app-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vibe-rag-app
  namespace: vibe-rag
spec:
  replicas: 2
  selector:
    matchLabels:
      app: vibe-rag-app
  template:
    metadata:
      labels:
        app: vibe-rag-app
    spec:
      containers:
        - name: app
          image: your-registry/vibe-rag-app:latest
          ports:
            - containerPort: 8000
          env:
            - name: GOOGLE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: vibe-rag-api
                  key: GOOGLE_API_KEY
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: vibe-rag-postgres
                  key: POSTGRES_PASSWORD
            - name: DATABASE_URL
              value: "postgresql://vibe:$(POSTGRES_PASSWORD)@postgres-headless.vibe-rag.svc.cluster.local:5432/vibe_rag"
            - name: COLLECTION_NAME
              valueFrom:
                configMapKeyRef:
                  name: vibe-rag-config
                  key: COLLECTION_NAME
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 30
          resources:
            requests:
              cpu: "250m"
              memory: "256Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
```

Apply:

```bash
kubectl apply -f app-deployment.yaml
```

---

## 7. Deploy Commands

Deploy everything in the correct order:

```bash
# 1. Namespace
kubectl create namespace vibe-rag

# 2. Secrets (fill in actual values)
kubectl create secret generic vibe-rag-api \
  --namespace vibe-rag \
  --from-literal=GOOGLE_API_KEY="<your-key>"

kubectl create secret generic vibe-rag-postgres \
  --namespace vibe-rag \
  --from-literal=POSTGRES_PASSWORD="<strong-password>"

# 3. Database
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f postgres-service.yaml

# Wait for the database to be ready
kubectl wait --namespace vibe-rag \
  --for=condition=ready pod \
  --selector=app=postgres \
  --timeout=120s

# 4. Application config and deployment
kubectl apply -f app-configmap.yaml
kubectl apply -f app-deployment.yaml

# 5. Check rollout
kubectl rollout status deployment/vibe-rag-app --namespace vibe-rag
```

To update the application image:

```bash
kubectl set image deployment/vibe-rag-app \
  app=your-registry/vibe-rag-app:new-tag \
  --namespace vibe-rag

kubectl rollout status deployment/vibe-rag-app --namespace vibe-rag
```

Roll back if needed:

```bash
kubectl rollout undo deployment/vibe-rag-app --namespace vibe-rag
```

---

## 8. Resource Sizing

Starting recommendations — tune based on observed CPU/memory usage.

| Component | Requests CPU | Requests Memory | Limits CPU | Limits Memory |
|-----------|-------------|-----------------|-----------|----------------|
| PostgreSQL (1 replica) | 500m | 512Mi | 2 | 2Gi |
| Application (2 replicas) | 250m | 256Mi | 1 | 1Gi |

**PostgreSQL notes:**
- The pgvector HNSW index build is CPU-intensive; allocate at least 1 core during
  initial ingestion of large corpora.
- Memory should be sized to hold the working set of the index in
  `shared_buffers` + OS page cache. A rule of thumb is 25% of node RAM for
  `shared_buffers`.

**Application notes:**
- Embedding batch calls to the Gemini API are network-bound; CPU usage is low.
- Memory scales with the number of concurrent requests in flight; 256Mi is sufficient
  for a single-threaded asyncio event loop.

---

## 9. pgvector Index Maintenance

Over time, as documents are added and deleted, the pgvector index may need rebuilding
for optimal performance.

### Check index size

```bash
kubectl exec -n vibe-rag \
  $(kubectl get pod -n vibe-rag -l app=postgres -o jsonpath='{.items[0].metadata.name}') \
  -- psql -U vibe -d vibe_rag -c "
    SELECT
      relname AS table,
      pg_size_pretty(pg_total_relation_size(oid)) AS total_size,
      pg_size_pretty(pg_indexes_size(oid)) AS index_size
    FROM pg_class
    WHERE relname LIKE '%documents%'
    ORDER BY pg_total_relation_size(oid) DESC;
  "
```

### Rebuild the ivfflat/hnsw index

If retrieval quality degrades after heavy writes, rebuild the index online with:

```bash
kubectl exec -n vibe-rag \
  $(kubectl get pod -n vibe-rag -l app=postgres -o jsonpath='{.items[0].metadata.name}') \
  -- psql -U vibe -d vibe_rag -c "
    REINDEX INDEX CONCURRENTLY documents_embedding_idx;
  "
```

`CONCURRENTLY` avoids locking the table during the rebuild (PostgreSQL 12+).

### Vacuum after large deletes

After deleting many documents, run `VACUUM` to reclaim storage and update planner
statistics:

```bash
kubectl exec -n vibe-rag \
  $(kubectl get pod -n vibe-rag -l app=postgres -o jsonpath='{.items[0].metadata.name}') \
  -- psql -U vibe -d vibe_rag -c "VACUUM ANALYZE documents;"
```

Enable `autovacuum` (PostgreSQL default) to handle this automatically in production.
