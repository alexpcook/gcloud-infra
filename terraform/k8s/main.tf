locals {
  manifests = fileset("${path.module}/apps", "**")
}

resource "kubernetes_namespace" "this" {
  for_each = toset([
    for manifest in local.manifests : dirname(manifest)
  ])

  metadata {
    name = each.key
  }
}

resource "kubernetes_manifest" "this" {
  for_each = local.manifests

  manifest = yamldecode(file("apps/${each.key}"))

  depends_on = [
    kubernetes_namespace.this
  ]
}
