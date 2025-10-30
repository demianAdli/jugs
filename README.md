# JUGS

**Joint Utility for Generic carbon-emission Simulation (JUGS)** is a software framework designed to evaluate carbon emissions in a **sector-based** manner.  
The framework follows a **microservices architecture**, in which each independent module operates as an autonomous service—referred to as a _jug_.

### Current Services

- **`jug_ee`** — A service that evaluates carbon emissions for the **Embodied** and **End-of-Life** stages of a building’s Life Cycle Assessment (LCA).
- **`jug_gis`** — A geospatial data-cleaning service built upon the _Object-Oriented Geographic Information System for Cities_ (**CityGISOO**) tool. This service currently comprises five components.
- **`jug_chassis`** — A foundational service providing shared modules used by other jugs. Unlike the other services, which communicate via APIs, `jug_chassis` can be installed and directly imported as a package to support development.

### Development and Collaboration

The project’s **business-value components** have been developed in collaboration with **domain experts**, who are cited in the corresponding repositories.  
The **design and development** of the overall project have been led by **Alireza Adli**.

A mirrored version of this project is hosted on the **Next-Generation Cities Institute (NGCI)** version-control platform, **Gitea**, at Concordia University.
