# template app


# vars :: {"template app": "project.name.lower_case"}


## linux setup
* when installing python deps, do not install as editable module

* On debian/ubuntu

	apt install -y python3.12-venv uwsgi uwsgi-plugin-python3 mediainfo ffmpeg

* add `CONFIG_FILE=uwsgi-linux.yaml` to `.env`

digital ocean notes
* load balancer
	* proxy mode --> disabled

## deployment steps
1. ssh into server
1. `su <user>`
1. `cd <root of this repo>`
1. `source .venv/bin/activate`
1. `git pull`
1. `pip install --upgrade mspec`
1. `cd templates/sosh-net/`
1. `./server.sh restart`