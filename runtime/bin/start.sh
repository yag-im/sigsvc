#!/usr/bin/env bash

GRACEFUL_STOP_SLEEP=${GRACEFUL_STOP_SLEEP:-30}

startup_app() {
    # Make sure your app will pass the health checks you've defined in consul when starting up, or whatever is the equivalent for your app
    # example: touch $APP_HOME_DIR/enabled.txt

    touch $APP_HOME_DIR/enabled.txt

    # Actually start up your app here, make sure you prefix the command with `exec` to ensure the app receives the SIGTERM

    exec $APP_HOME_DIR/bin/cmd.sh
}

disable_app() {
    # Don't actually stop your app here, the SIGTERM signal will be forwarded to your app
    # Just make your app fail health checks without actually shutting down
    # example: rm $APP_HOME_DIR/enabled.txt

    rm $APP_HOME_DIR/enabled.txt
}


# ==== DON'T EDIT BELOW THIS LINE ====
clean_stop() {
    disable_app
    sleep $GRACEFUL_STOP_SLEEP
    kill "$child_pid"
}

trap clean_stop SIGTERM
startup_app &
child_pid=$!
wait "$child_pid"
