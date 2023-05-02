using QarnotSDK;

var token = Environment.GetEnvironmentVariable("QARNOT_TOKEN");
var url = Environment.GetEnvironmentVariable("QARNOT_URL");

var connection = new Connection(url, token);

// Create an auto-scaling policy, based on the number of tasks queued on the pool. It encodes
// the following rules:
//  - minIdleSlots: have at least 4 idle slots at any time, so that we can absorb 4 tasks immediately
//    without needing to wait for machines to boot. When those idle slots are used, Qarnot's
//    scheduler will start provisioning new machines so as to maintain the minimum count of idle slots
//  - scale up to a maximum of 128 slots (maxTotalSlots)
//  - consider that a slot is inactive after 90 seconds being unused by any task, making it eligible
//    for termination, to scale the pool back down (minIdleTimeSeconds)
//  - scaling by at most 0.2 time maxTotalSlots at every scale up, every 90 seconds (scalingFactor)
//
// This policy is always enabled (TimePeriodAlways), meaning that it will match at any given time and
// date. Hence, it should be the last in the Policies list, used as a default policy. Being always
// enabled, any policy further in the list will always be ignored, and is hence useless.
//
// In this sample, the idea is that this is the scaling policy of the pool during times were we don't
// expect a lot of load (hence a low minIdleSlots), but we still want to be reactive to absorb some
// load spike that may arise, up to a maximum consumption of compute resources (128 slots).
var autoElasticDefaultPolicy = new ManagedTasksQueueScalingPolicy(
    name: "auto-elastic-default-policy",
    enabledPeriods: new() {
        new TimePeriodAlways("always")
    },
    minTotalSlots: 4,
    maxTotalSlots: 128,
    minIdleSlots: 4,
    minIdleTimeSeconds: 90,
    scalingFactor: 0.2f);


// Create a fixed policy, specifying a fixed amount of 512 slots to be up at all times.
// This policy is enabled every monday mornings from 6am to 12am, and every other weekday
// from 6am to 10am. This would typically be used to absorb predictible load spikes which
// happen at those times, without waiting for the automated scale-up to kick in, and without
// taking the risk of a pool scale down caused by some inactivity time during the expected
// load spike period.
//
// NOTE: start and end times are expresses as UTC, and MUST be formatted according to ISO-8601
var morningSpikePolicy = new FixedScalingPolicy(
    name: "morning-spikes-policy",
    enabledPeriods: new() {
        new TimePeriodWeeklyRecurring(
            name: "monday-mornings-extended",
            days: new() { DayOfWeek.Monday },
            startTimeUtc: new TimeOnly(6, 00, 0).ToString("o"),
            endTimeUtc: new TimeOnly(12, 0, 0).ToString("o")
        ),
        new TimePeriodWeeklyRecurring(
            name: "weekdays-mornings",
            days: new() { DayOfWeek.Monday, DayOfWeek.Tuesday, DayOfWeek.Wednesday, DayOfWeek.Thursday, DayOfWeek.Friday },
            startTimeUtc: TimeOnly.MinValue.ToString("o"),
            endTimeUtc: TimeOnly.MaxValue.ToString("o")
        )
    },
    slotsCount: 512
);


// NOTE: beware of order here! At any time, the first (in list order) matching policy will be
//       used, and all further policies are ignored. Hence, if you put the default policy first,
//       as it always matches, the morningSpikePolicy will never be active.
var scaling = new Scaling(new List<ScalingPolicy> {
    morningSpikePolicy,
    autoElasticDefaultPolicy
});



var pool = connection.CreatePool("scaling-sample", "docker-network", 1);
pool.Scaling = scaling;

await pool.StartAsync();
var poolUuid = pool.Uuid;


// Let's monitor the pool's currently enabled scaling policy.
//
// NOTE: there is a delay after submission after which the pool has not yet been submitted to the
//       main Qarnot scheduler, and after that during which the selection of the active policy has
//       not been made, or not reported to the frontend API. Hence, after submission, the active
//       policy will be seen as blank for some time.
//       The same way, there may be some delay between the time a given policy becomes active and
//       the time when it's reported to the frontend API and then refreshed by the SDK.
for (;;) {
    await pool.UpdateStatusAsync();
    Console.WriteLine($"Active scaling policy name: '{pool.Scaling.ActivePolicyName}' => {pool.Scaling.ActivePolicy}");
    await Task.Delay(TimeSpan.FromSeconds(5));
}

// As reference, here is how you would update the scaling specification of a pool
async Task UpdatePoolScaling(QPool pool)
{
    // Let's say that there is now a constant load of the pool and that 256 slots
    // is a count that fits the needs at any time
    //
    var newFixedPolicy = new FixedScalingPolicy(
        name: "single-policy",
        enabledPeriods: new() {
            new TimePeriodAlways("always")
        },
        slotsCount: 256
    );

    var newScaling = new Scaling(new() { newFixedPolicy });
    await pool.UpdateScalingAsync(newScaling);
}
