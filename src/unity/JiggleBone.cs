// JiggleBone — spring-damper secondary motion for hair / cloth bones.
// Attach to the HairB_1..3 / HairL_1..2 / HairR_1..2 / Robe_F/B/L/R
// bones of Ghost_Woman (optional: the baked clips already sway; this
// adds physics reacting to the ghost's actual movement and turns).
// Dependency-free; runs in LateUpdate after Mecanim writes the pose.

using UnityEngine;

public class JiggleBone : MonoBehaviour
{
    [Tooltip("How fast the bone catches up (higher = stiffer).")]
    public float stiffness = 120f;
    [Tooltip("Oscillation damping (0.22 = floppy ghost cloth).")]
    [Range(0.01f, 1f)] public float damping = 0.22f;
    [Tooltip("Gravity sag multiplier on the simulated tip.")]
    public float gravity = 1.5f;
    [Tooltip("Max swing away from the animated pose, degrees.")]
    public float limitDegrees = 40f;

    Transform _bone;
    Vector3 _tip;      // simulated world position of the bone's tip
    Vector3 _tipVel;
    float _len;

    void Start()
    {
        _bone = transform;
        // segment length: to the first child bone, or the parent's
        // segment for chain tips (uniform-length chains)
        if (_bone.childCount > 0)
            _len = Vector3.Distance(_bone.position,
                                    _bone.GetChild(0).position);
        else if (_bone.parent != null)
            _len = Vector3.Distance(_bone.position, _bone.parent.position);
        if (_len < 1e-4f) _len = 0.12f;
        _tip = _bone.position + _bone.up * _len;
        _tipVel = Vector3.zero;
    }

    void LateUpdate()
    {
        Vector3 anchor = _bone.position;
        Vector3 rigidTip = anchor + _bone.up * _len;

        Vector3 accel = (rigidTip - _tip) * stiffness
                        - _tipVel * (damping * 12f)
                        + Physics.gravity * gravity;
        _tipVel += accel * Time.deltaTime;
        _tip += _tipVel * Time.deltaTime;

        // keep the simulated tip at a fixed distance (bones can't stretch)
        Vector3 dir = _tip - anchor;
        float mag = dir.magnitude;
        dir = mag < 1e-5f ? _bone.up : dir / mag;
        float swing = Vector3.Angle(_bone.up, dir);
        if (swing > limitDegrees)
            dir = Vector3.Slerp(_bone.up, dir,
                                limitDegrees / swing).normalized;
        _tip = anchor + dir * _len;

        _bone.rotation = Quaternion.FromToRotation(_bone.up, dir)
                         * _bone.rotation;
    }

    void OnValidate()
    {
        if (stiffness < 1f) stiffness = 1f;
        if (limitDegrees < 5f) limitDegrees = 5f;
    }
}
