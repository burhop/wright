# Data Model: Community Release Readiness

## Use Case

Represents a target audience and their goal for trying, installing, developing, evaluating, or funding Wright.

**Fields**:

- `name`: Human-readable use case name.
- `audience`: Primary person or organization type.
- `goal`: What the user is trying to accomplish.
- `recommended_path`: The first path public docs should recommend.
- `prerequisites`: Required local software, accounts, hardware, credentials, or knowledge.
- `verification_step`: Observable success check.
- `known_limitations`: Platform, feature, or alpha-status caveats.
- `canonical_doc`: Public document or section that owns the guidance.

**Validation rules**:

- Every listed use case must have exactly one recommended first path.
- Every recommended path must have a verification step.
- Limitations must be explicit when support is partial, unvalidated, or dependent on external tools.

## Distribution Channel

Represents a public mechanism used to obtain Wright or a Wright component.

**Fields**:

- `channel_type`: Container, Python package, source checkout, Hermes plugin, native desktop package, or documentation-only path.
- `public_name`: Registry/project/image/package name.
- `owner`: Account or organization responsible for publishing.
- `audience`: User groups served by this channel.
- `status`: Planned, test, alpha, stable, deprecated, or unavailable.
- `supported_platforms`: Platform support claims and validation status.
- `versioning_policy`: Tag, release, or package version expectations.
- `verification_step`: Command or review step that proves the channel works.
- `canonical_links`: Repository, docs, release notes, issues, security, and funding links.

**Validation rules**:

- No channel may be documented as stable until a verification step exists.
- Package or image names must not be promised until ownership or availability is confirmed.
- Container platform claims must distinguish validated support from intended support.

## Public Listing

Represents a public entry surface where users discover Wright.

**Fields**:

- `surface`: Repository, docs site, package registry, container registry, release page, announcement, or ecosystem listing.
- `headline`: Short positioning statement.
- `audience`: Primary reader.
- `primary_action`: Try, install, contribute, sponsor, or contact.
- `required_links`: Canonical links to repo, docs, issues, security, releases, and funding/support.
- `status_message`: Alpha/stability and support expectation.
- `metrics`: Visibility indicators available from or related to the surface.

**Validation rules**:

- Each listing must state public-alpha or stability status when relevant.
- Each package/container listing must route users back to canonical documentation and security information.

## Funding Channel

Represents a way to provide money, hardware, credits, services, or paid work to Wright.

**Fields**:

- `channel_name`: Sponsorship, fiscal host, commercial support, partner program, hardware donation, cloud/API credit, or customer engagement.
- `provider`: Platform, company, or maintainer entity.
- `audience`: Individual, company, partner, or customer.
- `status`: Active, planned, application needed, blocked, or deferred.
- `funding_use`: What the resource pays for.
- `requirements`: Setup, eligibility, tax, legal, or application requirements.
- `public_contact`: Sponsorship or contact path.
- `disclosure`: Public statement explaining use of funds or resources.

**Validation rules**:

- Active funding paths must have a public contact or sponsor link.
- Planned funding paths must not imply availability.
- Funding uses must map to real Wright work categories.

## Partner Brief

Represents the outreach packet for hardware, cloud, or ecosystem programs.

**Fields**:

- `target_partner`: Company, program, or ecosystem.
- `value_proposition`: Why Wright matters to the partner.
- `requested_support`: Funding, hardware, credits, technical help, co-marketing, or validation access.
- `evidence`: Screenshots, demos, release status, architecture, or validation notes.
- `next_action`: Application, intro request, meeting, or follow-up.

**Validation rules**:

- Partner claims must not exceed validated Wright capabilities.
- Vendor-specific claims must remain separate from core install requirements.

## Visibility Indicator

Represents a measurable signal used after launch.

**Fields**:

- `name`: Metric name.
- `source`: Where the metric is observed.
- `cadence`: How often maintainers review it.
- `target`: Optional launch or growth target.
- `interpretation`: What the signal means and what action it might trigger.

**Validation rules**:

- At least five indicators must be defined before launch.
- Indicators should cover discovery, install, contribution, and funding signals.
