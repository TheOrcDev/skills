# Gaits

`motion.py` is pure Python: `foot_cycle`, `travel_speed`, `gait_phases`,
`support_count`, `body_bounce`, `wing_flap`, `lift_from_flap`, `chain_lag`.
Positions are fractions of body height; the authoring layer scales them.

## Foot cycle

Stance (phase < duty): the foot moves backward relative to the body at
constant speed from +stride/2 to -stride/2. That is what makes an in-place
clip read as planted when the actor travels at the implied speed.
Swing: cubic Hermite arc whose end slopes match the stance velocity, so
lift-off and touchdown have no velocity discontinuity. Clearance is a
sine-squared arc so vertical velocity is zero at both contacts.

Implied speed = stride / (duty x cycleSeconds). Record it as nominal speed.

## Phase tables

| Gait | Legs | Phases |
|---|---|---|
| trot | FL RR FR RL | diagonal pairs together: FL 0, RR 0, FR 0.5, RL 0.5 |
| walk | four-beat lateral | RR 0, FR 0.25, RL 0.5, FL 0.75 |
| bound | scurry | FL 0, FR 0.1, RL 0.5, RR 0.6 |
| biped | L R | L 0, R 0.5 |
| tripod | six legs | FL MR RL at 0; FR ML RR at 0.5 |
| tetrapod | eight legs | L1 R2 L3 R4 at 0; R1 L2 R3 L4 at 0.5 |
| flap | wings | downstroke to 0.4 of the cycle, recovery over 0.6; lift rises on the downstroke |

`support_count(kind, duty)` gives the minimum planted legs across the cycle.
Trot at duty 0.45 drops to 0 briefly (a real trot has a suspension phase);
raise duty for heavy bodies.

## Body

`body_bounce` is lowest at each support beat and highest between; pitch and
roll follow it. Tails, antennae and ears use `chain_lag` so later links lag
the base.

## Species notes from review

- Rat: low scurry (`bound`), credible paw lift, spine and head coordinated, tail follows direction changes.
- Wolf: trot with a jaw bone added for the bite; collapse death.
- Boar: heavier duty, tusk hook attack.
- Elder beast: four-beat walk, slam attack.
- Ants and spiders: tripod and tetrapod with the body stable; deaths curl.
- Flyers: in-place flap, engine supplies hover offset; deaths descend once to the real ground and stop.
