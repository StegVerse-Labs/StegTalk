# StegTalk Entity Runtime v1

## Purpose

StegTalk Entity Runtime v1 defines the first practical runtime loop for StegTalk and the broader StegVerse ecosystem.

It treats humans, AI entities, applications, repositories, services, communities, organizations, and governance nodes as addressable entities with shared runtime behavior.

The goal is to replace platform-owned accounts, app-store installs, opaque feeds, advertising profiles, and hidden permissions with a local-first, receipt-backed relationship model.

## Done Definition

This runtime pass is complete when StegTalk can represent and execute the following loop:

```text
Create
Publish
Discover
Recognize
Rely
Compensate
Message
Feed
Revoke
Fork
Credit lineage
Split contributor revenue
Update contributor policy safely
```

The minimum operating model is:

```text
Identity
Declaration
Recognition
Reliance
Receipt
Evaluation
Relationship Contract
Change Request
Commitment
Transition
```

Everything else is derived from those primitives.

---

## 1. Core Primitives

### Identity

An identity is the stable anchor for an entity.

Examples:

```text
Rigel
Auri
Chad
StegWeather
KnowledgeVault
SV-001
SV-002
StegVerse-Labs
```

Identity is not location, storage, provider, model, GitHub repository, device, or endpoint.

### Declaration

A declaration describes what an entity claims about itself.

Declarations may include:

```text
purpose
capabilities
boundaries
promises
version policy
lineage
compensation model
```

### Recognition

Recognition means an identity acknowledges another identity exists.

Recognition does not mean reliance, payment, permission, governance, or authority.

### Reliance

Reliance means one identity uses another identity for a purpose under a relationship contract.

Reliance may activate permissions, compensation, messaging scopes, and receipts.

### Receipt

A receipt proves that something happened, was committed, changed, settled, sent, revoked, forked, or evaluated.

Receipts preserve reconstructability without requiring all full state to be duplicated everywhere.

### Evaluation

Evaluation compares declarations, expectations, conditions, state, and receipts.

Evaluation answers questions such as:

```text
Is this ready?
Is this admissible?
Is this trusted?
Is this healthy?
What is missing?
Why did this reach my attention?
```

---

## 2. Entity Card Schema

The Entity Card is the universal contact/info page for every entity.

```yaml
entity_card:
  identity:
    id:
    display_name:
    type:
    alias:
    lineage:

  declarations:
    purpose:
    capabilities:
    boundaries:
    promises:
    version_policy:

  relationship:
    recognition:
      status:
      since:
    reliance:
      status:
      scope:
      terms:
    representation:
      allowed:
      representative:
    compensation:
      model:
      rate:
      recipient:

  state:
    local_status:
    published_status:
    active_users:
    active_reliance_count:

  receipts:
    latest:
    chain_head:
```

### StegWeather Example

```yaml
entity_card:
  identity:
    id: stegweather
    display_name: StegWeather
    type: service
    alias: StegWeather
    lineage: Rigel/StegWeather

  declarations:
    purpose: personalized weather intelligence
    capabilities:
      - forecasts
      - local alerts
      - user messaging
    boundaries:
      - not emergency dispatch
      - not official government alert authority
    promises:
      - severe weather alerts when configured and available
    version_policy: newest_stable

  relationship:
    recognition:
      status: recognized
      since: null
    reliance:
      status: active
      scope: local_device
      terms: stegweather_public_reliance_v1
    representation:
      allowed: false
      representative: null
    compensation:
      model: per_active_reliance
      rate: contract_defined
      recipient: primary_developer

  state:
    local_status: installed
    published_status: optional
    active_users: 1
    active_reliance_count: 1

  receipts:
    latest: null
    chain_head: null
```

---

## 3. Relationship Contract Schema

A Relationship Contract defines what two identities may do with each other.

It replaces scattered concepts such as app permissions, notification settings, terms of service, subscription settings, creator monetization, and support-channel rules.

```yaml
relationship_contract:
  parties:
    user_identity:
    entity_identity:

  relationship_type:
    - recognition
    - reliance
    - representation
    - subscription
    - stewardship
    - contributor

  scope:
    local
    private
    group
    public

  permissions:
    may_message:
    may_notify:
    may_read_local_state:
    may_write_local_state:
    may_request_payment:
    may_publish_updates:
    may_represent_user:

  compensation:
    model:
      none | per_use | per_active_reliance | subscription | donation
    rate:
    recipient:
    settlement_token:

  boundaries:
    cannot_sell_personal_data: true
    cannot_export_private_state_without_permission: true
    cannot_execute_consequence_without_authority: true

  receipts:
    created:
    updated:
    chain_head:
```

### StegWeather Reliance Contract Example

```yaml
relationship_contract:
  parties:
    user_identity: Sarah
    entity_identity: StegWeather

  relationship_type:
    - recognition
    - reliance

  scope: local

  permissions:
    may_message: true
    may_notify: severe_weather_only
    may_read_local_state:
      - location_region
      - weather_preferences
    may_write_local_state: false
    may_request_payment: true
    may_publish_updates: true
    may_represent_user: false

  compensation:
    model: per_active_reliance
    rate: contract_defined
    recipient: primary_developer
    settlement_token: StegCoin

  boundaries:
    cannot_sell_personal_data: true
    cannot_export_private_state_without_permission: true
    cannot_execute_consequence_without_authority: true
```

Core rule:

```text
Exit must be as clear as entry.
```

---

## 4. Change Request Lifecycle

A Change Request is the universal movement object.

Auri may create, interpret, or route Change Requests, but it does not silently execute consequence.

```yaml
change_request:
  id:
  requester:
  target_entity:
  relationship_contract_ref:
  requested_change:
    type:
    scope:
    reason:
  required_conditions:
  current_readiness:
  evaluation_refs:
  status:
    draft | ready | blocked | committed | executed | denied
  receipts:
    created:
    committed:
    executed:
```

Example requests:

```text
Recognize StegWeather
Rely on StegWeather
Publish StegWeather
Fork StegWeather
Upgrade Chad to newest model
Allow Auri to represent me for weather alerts
```

Lifecycle:

```text
User intent
→ Change Request
→ Readiness Evaluation
→ Authority Evaluation if needed
→ Commitment Receipt
→ Transition Receipt
→ Updated Entity Card / Relationship Contract
```

Important distinctions:

```text
Not ready ≠ denied.
Denied ≠ failed.
Blocked ≠ impossible.
Approval ≠ commitment.
Commitment ≠ execution.
Execution ≠ admissibility.
```

---

## 5. Evaluation Schemas

### Readiness Evaluation

Readiness determines whether a requested change has all required conditions satisfied.

```yaml
readiness_evaluation:
  change_request:
  target_entity:
  required_conditions:
    - recognition_present
    - relationship_contract_present
    - scope_defined
    - compensation_terms_defined
    - authority_present_if_required
    - capability_available
  observed_conditions:
  result:
    ready | not_ready | blocked | denied
  missing_conditions:
  confidence:
  receipts:
```

Example:

```yaml
result: not_ready
missing_conditions:
  - publication_scope
  - compensation_terms
  - update_policy
```

### Authority Evaluation

Authority Evaluation determines whether consequence may become binding.

```yaml
authority_evaluation:
  change_request_ref:
  actor:
  target_entity:
  scope:
  authority_basis:
  standing_result:
  authority_result:
    present | absent | conditional | denied
  conditions:
  confidence:
  receipt_ref:
```

Auri may request or explain authority evaluation, but Auri should not be the final consequence authority.

---

## 6. Receipt Types

### Commitment Receipt

A Commitment Receipt proves that consequence became binding.

```yaml
commitment_receipt:
  id:
  change_request_ref:
  readiness_evaluation_ref:
  authority_evaluation_ref:
  committed_by:
  committed_at:
  scope:
  binding_effect:
  conditions_locked:
  expires_at:
  receipt_chain_head:
```

### Transition Receipt

A Transition Receipt proves what actually changed.

```yaml
transition_receipt:
  id:
  commitment_receipt_ref:
  target_entity:
  transition_type:
  previous_state_ref:
  new_state_ref:
  executed_by:
  executed_at:
  execution_location:
  witnesses:
  result:
    success | partial | failed
  consequence_summary:
  receipt_chain_head:
```

### Recognition Receipt

```yaml
recognition_receipt:
  entity:
  recognized_by:
  local_alias:
  reliance_status:
  compensation_status:
  receipt_chain_head:
```

Recognition means:

```text
I acknowledge this entity exists.
Create a local Entity Card.
Do not rely on it yet.
Do not pay it yet.
Do not grant permissions yet.
```

### Reliance Receipt

```yaml
reliance_receipt:
  entity:
  relied_upon_by:
  scope:
  contract_ref:
  compensation_status:
  reliance_status:
  receipt_chain_head:
```

Reliance means:

```text
I use this entity for a purpose.
I accept its relationship contract.
It may perform the agreed capability.
Compensation may begin.
Receipts must prove the relationship.
```

### Compensation Settlement Receipt

```yaml
compensation_settlement_receipt:
  id:
  reliance_contract_ref:
  payer_identity:
  recipient_identity:
  entity_identity:
  settlement_model:
    per_active_reliance | per_use | subscription | donation
  token:
    StegCoin | StegToken
  amount:
  period:
  settled_at:
  result:
    success | pending | failed
  receipt_chain_head:
```

### Scoped Message Receipt

```yaml
scoped_message_receipt:
  id:
  sender_entity:
  message_ref:
  scope_used:
    developer_only | all_reliance_users | local_reliance_users | specific_group | public_feed
  recipient_basis:
    reliance_contract
    region_scope
    group_membership
    developer_relationship
  recipient_count:
  sent_at:
  delivery_result:
    success | partial | failed
  private_recipient_list_ref:
    local_or_encrypted_only
  receipt_chain_head:
```

Publicly visible example:

```text
StegWeather sent a regional severe-weather notice to 418 local reliance users.
```

Not publicly visible:

```text
Who those users are.
Their exact locations.
Their preferences.
Their usage history.
```

### Feed Item Receipt

```yaml
feed_item_receipt:
  id:
  feed_type:
    private | public | recipient | event | local | governance | developer

  source:
    source_type:
      message | scoped_message | transition | compensation | proposal | discussion | alert
    source_ref:

  visible_to_basis:
    public
    owner_only
    reliance_contract
    region_scope
    group_membership
    authority_scope

  author_entity:
  created_at:
  receipt_chain_head:
```

### Attention Receipt

```yaml
attention_receipt:
  id:
  user_identity:
  source_entity:
  feed_item_ref:
  delivery_scope:
  feed_control_rule_applied:
  attention_reason:
    emergency_override
    user_allowed_scope
    active_reliance_contract
    developer_relationship
    governance_relevance
  delivered_at:
  user_action:
    viewed | dismissed | muted | escalated | replied
  receipt_chain_head:
```

### Revocation Receipt

```yaml
revocation_receipt:
  entity:
  reliance_status:
  compensation_status:
  recognition_status:
  local_data_status:
  receipt_chain_head:
```

### Fork Receipt

```yaml
fork_receipt:
  source_entity:
  new_entity:
  lineage_ref:
  reliance_status:
  upstream_compensation_status:
  receipt_chain_head:
```

### Split Settlement Receipt

```yaml
split_settlement_receipt:
  entity:
  revenue_source:
  settlement_period:
  gross_amount:
  token:

  active_split_policy_ref:

  distributions:
    - recipient:
      role:
      share:
      amount:
      result:
        success | pending | failed

  upstream_distributions:
    - upstream_entity:
      share:
      amount:
      result:

  infrastructure_distribution:
    recipient:
    share:
    amount:
    result:

  settled_at:
  receipt_chain_head:
```

---

## 7. Discovery Record

A Discovery Record is the public or scoped listing for an entity.

It exposes only what others need to recognize and rely on the entity.

```yaml
discovery_record:
  entity_id:
  display_name:
  type:
  purpose:
  capabilities:
  boundaries:
  lineage:
  visibility:
  recognition_count:
  reliance_count:
  compensation_model:
  relationship_contract_template_ref:
  latest_public_receipt_ref:
```

The Discovery Record should not expose:

```text
Personal user data
Private configuration
Local forecast preferences
Device data
Private messages
Subscriber identities
```

It only exposes:

```text
What this entity is
What it offers
What it does not claim
How many rely on it
How to begin a relationship
```

---

## 8. Feed, Message, and Attention Rules

### Message Scope Rules

```yaml
message_scope_rules:
  sender_entity:
  allowed_scopes:
    - developer_only
    - all_reliance_users
    - local_reliance_users
    - specific_group
    - public_feed

  prohibited_scopes:
    - hidden_targeting
    - behavioral_advertising
    - personal_data_export

  required_receipts:
    - message_sent
    - scope_used
    - recipient_group_basis
```

Core boundary:

```text
Scoped messaging is allowed.
Hidden profiling is not.
```

### Feed View Rules

```yaml
feed_view_rules:
  feed_type:
    private | public | recipient | event | local | governance | developer

  visibility_basis:
    owner_only
    public_discoverable
    reliance_contract
    location_scope
    relationship_scope
    authority_scope

  allowed_content:
    - messages
    - receipts
    - announcements
    - discussions
    - alerts
    - proposals
    - transitions

  prohibited_content:
    - hidden_ads
    - behavioral_targeting
    - unauthorized_private_state
```

Core rule:

```text
Feeds are lenses, not data owners.
```

### Visibility Explanation

Every feed item should answer why the user is seeing it.

```yaml
visibility_explanation:
  feed_item_ref:
  visible_because:
    - public_feed
    - reliance_contract
    - local_region_scope
    - group_membership
    - developer_relationship
    - authority_scope

  user_facing_text:
  receipt_ref:
```

Examples:

```text
You are seeing this because you rely on StegWeather for local severe-weather alerts.
```

```text
You are seeing this because StegWeather posted it to its public feed.
```

Core rule:

```text
No invisible reason for visibility.
```

### Feed Control Panel

```yaml
feed_control_panel:
  user_identity:
  global_defaults:
    public_feed: muted_by_default
    reliance_updates: allowed
    local_alerts: allowed
    governance_notices: allowed_if_relevant
    promotional_messages: denied

  entity_controls:
    StegWeather:
      public_feed: follow
      local_alerts: allow
      major_updates: allow
      developer_messages: allow_if_developer
      compensation_receipts: private_only

  quiet_rules:
    mute_noncritical_updates:
    allow_emergency_override:
    digest_frequency:
```

Core rule:

```text
Attention is user-governed.
```

---

## 9. Revocation, Data Exit, and Forking

### Revocation Request

```yaml
revocation_request:
  requester_identity:
  target_entity:
  relationship_contract_ref:
  revoke:
    - reliance
    - compensation
    - notifications
    - local_permissions
    - recognition
  effective_time:
    immediate | end_of_period
  preserve_receipts: true
```

Distinctions:

```text
Revoke reliance ≠ forget entity.
Revoke recognition = remove local contact.
Revoke permissions ≠ delete receipts.
```

### Data Exit Policy

```yaml
data_exit_policy:
  user_identity:
  target_entity:
  revoked_relationship_ref:

  local_state:
    personalization:
      keep | export | delete
    preferences:
      keep | export | delete
    cached_content:
      keep | delete
    generated_outputs:
      keep | export | delete
    forks:
      keep_active | archive | delete

  receipts:
    preserve: true
    visibility:
      private | contract_only | public_aggregate

  entity_permissions:
    revoke_read_access: true
    revoke_write_access: true
    revoke_notification_access: true
    revoke_payment_access: true
```

Core rule:

```text
Revocation ends the relationship.
It does not erase the user’s history or ownership.
```

### Fork Request

```yaml
fork_request:
  requester_identity:
  source_entity:
  source_relationship_ref:
  fork_type:
    personalization_only | full_local_fork | publishable_fork
  lineage_preservation: true
  compensation_policy:
    continue_upstream_share | stop_upstream_share | renegotiate
  receipts_required: true
```

Core rule:

```text
Forking preserves lineage without preserving dependence.
```

---

## 10. Lineage, Upstream Compensation, and Contributor Splits

### Lineage Credit Policy

```yaml
lineage_credit_policy:
  fork_entity:
  upstream_entity:
  lineage_ref:
  credit_required: true
  upstream_compensation:
    none | voluntary | percentage | fixed_share | time_limited
  attribution_visibility:
    private | public | contract_only
```

Core rule:

```text
Lineage preserves credit.
Reliance determines compensation.
Forking does not erase origin.
```

### Contributor Split Policy

```yaml
contributor_split_policy:
  entity:
  revenue_source:
    active_reliance | per_use | subscription | donation | fork_upstream

  splits:
    primary_developer:
      identity:
      share:

    contributors:
      - identity:
        contribution_type:
        share:

    upstream_lineage:
      entity:
      share:

    ecosystem_infrastructure:
      share:

  update_rules:
    requires_contributor_approval:
    requires_governance_review:
    receipt_required: true
```

### Contributor Change Request

```yaml
contributor_change_request:
  entity:
  requester:
  requested_change:
    add_contributor | remove_contributor | update_share | update_role
  reason:
  current_split_policy_ref:
  proposed_split_policy:
  required_approvals:
  readiness_evaluation_ref:
  commitment_receipt_ref:
  transition_receipt_ref:
```

Core rule:

```text
No contributor, split, lineage, or compensation change occurs silently.
```

---

## 11. Auri Routing Role

Auri is the user-facing navigator and context evaluator.

Auri should help determine:

```text
What is the user trying to do?
Which entity should receive the request?
What relationship exists?
What contract applies?
What conditions are missing?
What receipts prove the current state?
What requires user attention?
```

Auri should not be treated as:

```text
Final governance authority
Final consequence authority
Unbounded execution authority
```

Auri may represent a user only under scoped delegation.

Example:

```yaml
representation:
  represented_identity: Rigel
  representative_identity: Auri
  scope:
    - draft_change_requests
    - summarize_readiness
    - route_to_domain_entities
  excluded:
    - final_commitment
    - irreversible_execution
```

Auri can route by intent and context.

Example:

```text
User: Will it rain tomorrow?
Auri routes to: Weather domain / StegWeather
```

```text
User: Publish StegWeather.
Auri routes to: Change Request → Readiness Evaluation → Governance if needed
```

---

## 12. LLM Contacts

LLMs are entities and may appear as contacts.

Example:

```yaml
entity_card:
  identity:
    display_name: Chad
    type: ai_contact
    alias: Chad
    lineage: OpenAI/ChatGPT

  declarations:
    purpose: general AI assistance
    capabilities:
      - chat
      - drafting
      - reasoning
    boundaries:
      - no autonomous consequence authority
      - provider-dependent availability
    version_policy: newest_available

  relationship:
    recognition:
      status: recognized
    reliance:
      status: active
      scope: private
    compensation:
      model: provider_plan_or_stegverse_contract
```

Supported version policies:

```text
pin_version
newest_stable
newest_available
manual_selection
```

Auri is also an entity, but Auri is best understood as a persistent role/representative framework rather than a single model endpoint.

```text
Auri = persistent identity and context role
Model = replaceable execution component
```

---

## 13. Privacy Boundaries

The runtime is designed to avoid the personal-data economy.

Public aggregates may include:

```text
recognition_count
reliance_count
published_status
capability declarations
public receipts
```

Public aggregates must not include:

```text
user identities
private locations
behavioral profiles
usage histories
private messages
personal preferences
```

Core privacy rule:

```text
Useful adoption statistics do not require behavioral surveillance.
```

StegWeather can show:

```text
18 active reliance relationships
```

without exposing:

```text
who those users are
where they live
what they click
what they buy
what they believe
```

---

## 14. First Runtime Loop

The first complete runtime loop is:

```text
Entity Declaration
→ Entity Card
→ Discovery Record
→ Recognition
→ Reliance Contract
→ Compensation Settlement
→ Scoped Messaging
→ Feed Receipt
→ Attention Receipt
→ Revocation
→ Fork
→ Lineage Credit
→ Contributor Split
→ Split Settlement
→ Contributor Change Request
```

This loop supports:

```text
Create
Publish
Discover
Recognize
Rely
Compensate
Message
Feed
Revoke
Fork
Credit lineage
Split contributor revenue
Update contributor policy safely
```

---

## 15. Implementation Checklist

A minimal local-first prototype should implement:

```text
[ ] Entity Card JSON/YAML schema
[ ] Relationship Contract schema
[ ] Change Request schema
[ ] Readiness Evaluation schema
[ ] Commitment Receipt schema
[ ] Transition Receipt schema
[ ] Recognition Receipt schema
[ ] Reliance Receipt schema
[ ] Discovery Record schema
[ ] Revocation Receipt schema
[ ] Fork Receipt schema
```

The first prototype does not need full token settlement, public discovery, or external publishing.

The first prototype only needs to prove:

```text
Create Entity
Recognize Entity
Rely on Entity
Generate Receipts
Update Entity Card
Revoke Reliance
Preserve Receipts
```

---

## 16. Completion Statement

StegTalk Entity Runtime v1 is complete as a design artifact when it defines a coherent, receipt-backed loop for treating every person, AI, app, repository, service, community, organization, and governance node as an addressable entity with declarations, relationships, recognition, reliance, permissions, compensation, feeds, revocation, lineage, and receipts.

This document completes that first design pass.
