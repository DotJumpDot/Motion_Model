// GhostAI — minimal wander/chase/attack controller for the
// Motion_Model ghosts. Dependency-free (no NavMesh): moves the
// transform on the XZ plane, so the ground just needs a collider and
// the player GameObject needs the tag "Player".
//
// Animator wiring (see Docs/IMPORT_CHECKLIST.md):
//   bool "Walking"  — drives Idle <-> Walk (or Float)
//   trigger "Attack" — plays the Attack/Lunge clip once
// Clips are in-place; this script owns all root movement.

using UnityEngine;

public class GhostAI : MonoBehaviour
{
    enum State { Idle, Wander, Chase, Attack }

    [Header("References")]
    public Transform player;
    public string playerTag = "Player";

    [Header("Movement")]
    public float wanderRadius = 8f;
    public float walkSpeed = 1.2f;
    public float chaseSpeed = 2.6f;
    public float turnSpeed = 4f;

    [Header("Behavior")]
    public float detectRange = 10f;
    public float attackRange = 1.6f;
    public float attackCooldown = 2.5f;
    public float idleTime = 2f;

    static readonly int Walking = Animator.StringToHash("Walking");
    static readonly int Attack = Animator.StringToHash("Attack");

    Animator anim;
    State state = State.Idle;
    Vector3 home;
    Vector3 wanderTarget;
    float stateUntil;

    void Start()
    {
        anim = GetComponent<Animator>();
        home = transform.position;
        stateUntil = Time.time + idleTime;
    }

    void Update()
    {
        if (player == null)
        {
            GameObject p = GameObject.FindGameObjectWithTag(playerTag);
            if (p != null) player = p.transform;
        }

        float dist = player != null
            ? Vector3.Distance(transform.position, player.position)
            : float.MaxValue;

        switch (state)
        {
            case State.Idle:
                anim.SetBool(Walking, false);
                if (dist < detectRange) state = State.Chase;
                else if (Time.time > stateUntil) PickWanderTarget();
                break;

            case State.Wander:
                anim.SetBool(Walking, true);
                MoveTo(wanderTarget, walkSpeed);
                if (dist < detectRange) state = State.Chase;
                else if ((transform.position - wanderTarget)
                             .sqrMagnitude < 0.04f)
                {
                    state = State.Idle;
                    stateUntil = Time.time +
                        Random.Range(idleTime * 0.5f, idleTime * 1.5f);
                }
                break;

            case State.Chase:
                if (dist > detectRange * 1.5f)
                {
                    PickWanderTarget();
                    break;
                }
                anim.SetBool(Walking, true);
                MoveTo(player.position, chaseSpeed);
                if (dist < attackRange && Time.time > stateUntil)
                {
                    state = State.Attack;
                    anim.SetTrigger(Attack);
                    stateUntil = Time.time + attackCooldown;
                }
                break;

            case State.Attack:
                // The clip owns the lunge; stand still until the
                // cooldown expires, then go back to hunting.
                anim.SetBool(Walking, false);
                if (Time.time > stateUntil) state = State.Chase;
                break;
        }
    }

    void PickWanderTarget()
    {
        Vector2 r = Random.insideUnitCircle * wanderRadius;
        wanderTarget = home + new Vector3(r.x, 0f, r.y);
        state = State.Wander;
    }

    void MoveTo(Vector3 target, float speed)
    {
        target.y = transform.position.y;
        Vector3 dir = (target - transform.position);
        if (dir.sqrMagnitude > 0.0001f)
        {
            Quaternion look = Quaternion.LookRotation(dir.normalized);
            transform.rotation = Quaternion.Slerp(
                transform.rotation, look, turnSpeed * Time.deltaTime);
        }
        transform.position = Vector3.MoveTowards(
            transform.position, target, speed * Time.deltaTime);
    }
}
