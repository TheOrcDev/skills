# Gates

`gates.evaluate(review, mode, required)` returns a list of failures. Empty
means every technical gate passed. Passing is necessary, never sufficient.
Thresholds are fractions of body height (h) unless stated.

| Gate | Threshold | Catches |
|---|---|---|
| floorPenetration | 1% h (per-vertex allowance: a vertex may sink to the feet plane or its own rest depth) | Soles or bodies under the floor |
| frozen | mesh must move at least 0.1% h | A clip that did not bind |
| rootStationary | Root location zero, rotation identity, every frame | Navigation root drift |
| bodyScaleUnit | body bone scale 1 | Scale keys leaking into export |
| postureDrop | 10% (Idle, Locomotion) | Core region collapsing relative to the body bone |
| actionDrop | 30% (BasicAttack, Cast, Hit) | Detachment during actions |
| loopSeam | 0.5% h pose difference across the loop | Idle or walk that pops |
| seamAcceleration | seam at most 1.6x worst interior acceleration | Loop hitch |
| stanceDrift | 2% h planted-sole drift at nominal speed (Locomotion, ground) | Skating feet |
| minSwingClearance | 3% h | Feet dragging in swing |
| flapRange | wing tips move at least 25% h (air Idle and Locomotion) | Dead wings |
| deathCoreDrop | core drops at least 15% h, or keel-over (rotation at least 0.5 rad with at most 10% rise), or flyer wings down (within 20% h of ground) and still (3% h over the last fifth) | A death that does not die |
| deathSettle | last 20% of Death moves the core at most 5% h | Still moving at the end |
| deathSeam | Death ends at least 20% h from its start | Death looping back |
| weaponAngle | jaw or mandible opens at least 0.35 rad in BasicAttack and closes to 0.05 rad | Pecking, or a stuck jaw |
| distinct | no two clips share a displacement signature | Copy-pasted clips |

Death is exempt from region-drop detachment (a flat corpse drops every
region by design).

Locomotion without contact evidence in the receipt fails `stanceDrift`
with "no traveling contact evidence". That is the correct answer for a
foreign FBX; author or package the clip so contacts exist.

Change a threshold only with a recorded decision and a reason in the commit.
