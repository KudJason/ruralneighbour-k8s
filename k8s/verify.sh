#!/bin/bash

set -euo pipefail

NAMESPACE="${NAMESPACE:-default}"
TIMEOUT="${TIMEOUT:-60s}"
SERVICES=(auth-service user-service location-service request-service payment-service notification-service content-service safety-service)

log() {
  echo "[$(date '+%H:%M:%S')] $*"
}

header() {
  echo "\n==== $* ===="
}

check_context() {
  header "Kubernetes Context & Namespace"
  kubectl config current-context | sed 's/^/Context: /'
  echo "Namespace: ${NAMESPACE}"
}

rollout_and_status() {
  local deploy="$1"
  header "Deployment: ${deploy}"
  set +e
  kubectl rollout status deployment "${deploy}" -n "${NAMESPACE}" --timeout="${TIMEOUT}"
  local rc=$?
  set -e
  kubectl get deploy "${deploy}" -n "${NAMESPACE}" -o wide || true
  echo
  kubectl get pods -n "${NAMESPACE}" -l app="${deploy}" -o wide || true
  return ${rc}
}

latest_pod_name() {
  local selector="$1"
  kubectl get pods -n "${NAMESPACE}" -l "${selector}" --sort-by=.metadata.creationTimestamp -o name | tail -n 1 | sed 's#^pod/##'
}

dump_pod_details() {
  local deploy="$1"
  local pod
  pod=$(latest_pod_name "app=${deploy}")
  if [[ -n "${pod}" ]]; then
    header "Pod describe: ${pod}"
    kubectl describe pod -n "${NAMESPACE}" "${pod}" | tail -n 120 || true
    header "Pod logs (tail 120): ${pod}"
    kubectl logs -n "${NAMESPACE}" "${pod}" --tail=120 || true
  else
    log "No pods found for ${deploy}"
  fi
}

cluster_health() {
  header "Cluster Pods (backend tier)"
  kubectl get pods -n "${NAMESPACE}" -l tier=backend --sort-by=.metadata.creationTimestamp || true

  header "Recent Events"
  kubectl get events -n "${NAMESPACE}" --sort-by=.lastTimestamp | tail -n 30 || true
}

service_health_probe() {
  local name="$1"
  local path="${2:-/health}"
  header "In-cluster health probe: ${name}${path}"
  # Use curl container in cluster to hit ClusterIP Service on port 80
  set +e
  kubectl run "curl-${name}-$$" -n "${NAMESPACE}" --rm -i --restart=Never \
    --image=curlimages/curl:8.8.0 -- \
    -sS "http://${name}:80${path}" || true
  set -e
}

main() {
  check_context
  cluster_health

  local failures=0
  for svc in "${SERVICES[@]}"; do
    if rollout_and_status "${svc}"; then
      log "${svc} rollout OK"
    else
      log "${svc} rollout NOT ready within ${TIMEOUT}"
      failures=$((failures+1))
    fi
    dump_pod_details "${svc}"
    service_health_probe "${svc}" "/health"
  done

  header "Summary"
  if [[ ${failures} -eq 0 ]]; then
    echo "All deployments ready."
    exit 0
  else
    echo "${failures} deployment(s) not ready. See logs above."
    exit 1
  fi
}

main "$@"



