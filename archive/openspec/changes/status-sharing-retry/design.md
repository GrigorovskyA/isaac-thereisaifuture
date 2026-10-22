# Design

Write the same complete JSON temporary file once. Retry Path.replace only on
PermissionError with winerror5,32,33,using monotonic1s cap and10ms pacing. Keep prior
complete destination visible; never truncate it,skip publication or suppress a
persistent fault. Other failures propagate immediately. Child learner retains its
original fixed deadline throughout parent retries. Cleanup still publishes terminal
result. A read-sharing race is plausible,not proven root cause without a native
handle trace; reproduce actual Windows open-reader semantics in a test.
