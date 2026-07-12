# template app


# vars :: {"template app": "project.name.lower_case"}


## linux setup
when installing python deps, do not install as editable module

On debian/ubuntu

	apt install -y python3.12-venv uwsgi uwsgi-plugin-python3 mediainfo ffmpeg

`uwsgi.yaml` changes needed in linux:
* wrap `uwsgi.logformat` in double quotes
* change `uwsgi.http=<value>` to `uwsgi.http-socket=<value>`
* add `uwsgi.plugin: python3`
* add `uwsgi.pythonpath: /home/sosh/mspec/.venv/lib/python3.12/site-packages`

digital ocean notes
* load balancer
	* proxy mode --> disabled

## deployment steps
* from /home/sosh/mspec
* activate venv
* pull new changes
* run pip install again for mspec repo to install new version
* restart server
