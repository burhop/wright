# Reproduce the selected host's missing mutable dependency in a pinned image.
# This is a separate engineering runtime, never the Wright base image.
FROM leoyue123/foamagent@sha256:5c8bd752884b95b45c02d74a4b5e449fbf22aea8fa13a0eb1a40be851350ff1e
RUN /opt/conda/envs/FoamAgent/bin/python -m pip install --no-cache-dir gmsh==4.15.1
RUN /opt/conda/envs/FoamAgent/bin/python -c "import gmsh, pyvista; assert gmsh.__version__ == '4.15.1'; assert pyvista.__version__ == '0.44.2'"
