STEGTALK_HBBL_SPEC.md

StegTalk Human Body Bearer Layer (HBBL)
Using the human body as a secure, low-bandwidth conduit for StegTalk chunks

⸻

1. Purpose & Scope

The Human Body Bearer Layer (HBBL) defines how StegTalk can use the human body as a passive communication medium between devices, leveraging:
	•	Electro-quasistatic / body-coupled communication (HBC/BCC)
	•	Capacitive coupling via skin contact or near-contact
	•	Bone-conducted/acoustic micro-signaling (optional)

HBBL is not about turning the human body into a full radio.
It is a short-range, low-bandwidth, high-privacy link that:
	•	connects devices on or near the same body, or
	•	connects devices via physical touch (handshake, shared surface, etc.)

HBBL carries StegTalk chunks, not full messages.

⸻

2. Design Goals
	1.	Privacy-first
– Signals are extremely low-power, short-range, and hard to detect remotely.
	2.	Safety-first
– Below medical device and ECG safety thresholds.
	3.	Low bandwidth, high reliability
– Assume 10 bps – 10 kbps typical; optimize for robustness, not throughput.
	4.	Device-agnostic
– Wearables, phones, implants, rings, bands, ear-worn devices.
	5.	Seamless with multipath StegTalk
– HBBL is just one more bearer alongside BLE, WiFi Direct, QR, audio, etc.

⸻

3. Physical Channels & Modes

HBBL defines a few physical “modes”:

3.1. Skin Contact Mode (HBC / BCC)
	•	Devices couple via skin contact:
	•	watch ↔ phone
	•	ring ↔ ring (handshake)
	•	patch ↔ phone
	•	Signaling:
	•	low-frequency electro-quasistatic
	•	single-ended or differential coupling
	•	Range:
	•	typically within a single body
	•	or short paths (e.g., touch point between two people)

Use cases:
	•	Handshake → key exchange or StegTalk chunk transfer
	•	Phone unlock when user touches phone with authenticated body-worn device
	•	Private sharing of identity/StegID between two people

⸻

3.2. Body-to-Surface-to-Body Mode
	•	Person A touches conductive or semi-conductive surface (metal rail, door handle)
	•	Their device injects a micro-encoded StegTalk chunk through contact
	•	Surface retains the electrical modulation momentarily (more realistically: provides the coupling path)
	•	Person B touches the same surface soon after, device reads the signal pattern

Use cases:
	•	“Drop” a message into a doorknob; another person “picks it up” by touching it
	•	Very short, covert data exchange in controlled environments

⸻

3.3. Body-Assisted Near-Field Mode
	•	Devices couple inductively or capacitively near the body
	•	The body modifies field properties and provides a stable medium
	•	E.g., phone in pocket ↔ ring on finger ↔ touch pad

Use cases:
	•	Unlocking devices upon mere proximity + touch
	•	Device-to-device StegTalk chunk passing triggered by user contact

⸻

3.4. Bone-Conducted Acoustic Mode (Optional/Future)
	•	Use high-frequency (possibly ultrasonic) vibration through bone
	•	Device on wrist or behind ear sends encoded signals through skull or arm
	•	Another body-mounted device receives via accelerometer/mic

Use cases:
	•	Ultra-covert, extremely short-range messaging
	•	Authentication/channel bootstrapping

⸻

4. HBBL Protocol Overview

At the protocol level, HBBL is just another StegTalk bearer:
+--------------------------+
| StegTalk Message Layer   |
+--------------------------+
| Chunking & FEC Layer     |
+--------------------------+
| Bearer Abstraction Layer |
+--------------------------+
|   HBBL   |   BLE   | ... |
+--------------------------+

4.1. HBBL Chunk Structure
Each HBBL chunk is small, e.g.:

struct HBBLChunk {
    msg_id_hash      // truncated hash of message ID
    chunk_index      // which chunk this is
    fec_group_id     // for erasure coding group
    payload_bytes    // 8–64 bytes typical
    auth_tag         // MAC/signature fragment
}

Total size per HBBL transmission: ~16–128 bytes, adjustable.

⸻

4.2. Transmission Session
A “session” is a short burst of one or more chunks over HBBL, initiated by:
	•	direct touch event
	•	contact with a known surface
	•	explicit user action (tap to share, handshake confirm, etc.)

Session states:
	1.	Discover
– Sender detects potential receiver (e.g., capacitive/contact event).
	2.	Sync
– Optional training pattern to calibrate body/surface impedance.
	3.	Burst
– Sender transmits 1..N HBBLChunks.
	4.	Ack (optional)
– Receiver may send a short acknowledgment or additional request.
	5.	End
– Session terminates quickly (100ms – 5s typical).

All data is encrypted StegTalk chunk payload – HBBL does not see plaintext.

⸻

5. HBBL Encoder/Decoder Logic

Sender-side:
	1.	Accept StegTalk chunk from chunking layer.
	2.	Encode bytes into:
	•	amplitude shift, or
	•	frequency shift, or
	•	phase/pulse-position modulation
	3.	Drive output:
	•	HBC electrodes to skin, or
	•	actuator for bone conduction, etc.

Receiver-side:
	1.	Sample input (ADC, sensor).
	2.	Detect signal above noise threshold.
	3.	Demodulate to byte sequence.
	4.	Validate:
	•	basic checksum
	•	auth_tag/MAC
	5.	If valid → pass HBBLChunk up to StegTalk chunk layer.

⸻

6. Security & Threat Model

6.1. Threats
	•	Proximal eavesdropper
– Attacker very close to body or touch surface.
	•	Compromised device
– Malware on one endpoint.
	•	Side-channel inference
– Correlating touches with message transfer attempts.
	•	Replay
– Capturing a body-coupled signal and replaying it later.

6.2. Mitigations
	•	All HBBL chunks are:
	•	encrypted (no plaintext, ever)
	•	bound to single-use nonces
	•	signed/MAC’d at the StegTalk level
	•	Sessions can:
	•	use short-lived session keys
	•	time-limit acceptance (e.g., chunk valid for <30s)
	•	use interactive “tap pattern” or “touch shape” as second factor
	•	Replays:
	•	Nonce + timestamp + msg_id_hash prevent replay being accepted
	•	Replayed chunk will fail integrity / freshness checks
	•	Eavesdroppers:
	•	Even if they detect a signal and demodulate bytes, they see ciphertext
	•	Without StegID private keys, content is useless

⸻

7. Feasibility & Hardware Considerations

7.1. Near-Term (0–3 Years)
	•	Implementation via wearables:
	•	Smart rings
	•	Smartwatches
	•	Phone accessories / cases
	•	Use off-the-shelf:
	•	ADCs
	•	Low-voltage HBC front-ends
	•	Existing body-comms reference designs (research-derived)

Realistic bitrates: 100 bps – 10 kbps.
Enough for handshake, identity, small StegTalk chunks.

7.2. Mid-Term (3–7 Years)
	•	Integrated HBBL hardware modules in:
	•	phones
	•	wearables
	•	health devices
	•	Standardized skin-contact data pads (like contactless pads, but body-coupled)

7.3. Long-Term (>7 Years)
	•	Possible medical-grade implants and sub-dermal communicators
	•	Space/aero flight suits with built-in HBBL nodes
	•	Highly optimized modulation schemes for extremely low power

⸻

8. Example Use Cases
	1.	Handshake Authentication
	•	Two people wearing compatible devices shake hands.
	•	StegTalk chunks are exchanged via skin contact.
	•	Their devices now share out-of-band keys and message seeds.
	2.	Door Handle Drop
	•	User touches door handle; device sends a StegTalk chunk into the metal.
	•	Friend later touches the handle; their device reads the chunk.
	•	The chunk is part of a message assembled via other bearers as well.
	3.	Offline Identity Transfer
	•	Human A touches Human B’s wrist/hand.
	•	HBBL transfers StegID public key + a few identity-proof chunks.
	•	Their devices reconcile later over any bearer.
	4.	Privacy-Preserving Check-in
	•	In a hospital or secure site, user touches a pad.
	•	HBBL transfers signed presence proof.
	•	No radio broadcast; no visible transfer.

⸻

9. Patentable Elements (Brainstorm Outline)

If you choose to pursue IP around this, potential claim areas:
	1.	Method for splitting encrypted communication into bearer-agnostic chunks and transmitting subsets through body-coupled pathways while maintaining end-to-end cryptographic integrity.
	2.	System for using the human body as an opportunistic, low-bandwidth, multi-factor communication channel for message reconstruction in a multi-bearer mesh network.
	3.	Method of combining body-coupled communication with optical/audio/emoji-based chunk routing for resilient, censorship-resistant messaging.
	4.	AI-based endpoint logic that assesses completeness and integrity of messages assembled from body-coupled and non-body-coupled bearers, determining safe display vs deferral.
	5.	Techniques for encoding StegTalk message identifiers and chunk indices in electro-quasistatic body-coupled signals with forward error correction and time-bounded validity.

(Obviously a patent attorney would need to structure claims — but this is the conceptual “bones.”)

⸻

10. Integration With StegTalk Spec

HBBL fits cleanly as:
	•	another Bearer implementation in the StegTalk stack
	•	invoked when:
	•	user enables “body-contact transfer”
	•	device detects skin contact events
	•	device policy allows HBBL participation

No changes to StegTalk’s core cryptography are required.
