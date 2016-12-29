#!/bin/bash
 
NAME="EQL"
FLASKDIR=/EQL
SOCKFILE=/EQL/sock
USER=root
GROUP=root
NUM_WORKERS=10
 
echo "Starting $NAME"
 
# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR
 
# Start your gunicorn
exec gunicorn router_main:app -b 127.0.0.1:5000 \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE
