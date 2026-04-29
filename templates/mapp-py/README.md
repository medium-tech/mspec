# template app


# vars :: {"template app": "project.name.lower_case"}


## linux setup
when install python deps, do not install as editable module

On debian/ubuntu

	apt install -y python3.12-venv uwsgi uwsgi-plugin-python3 mediainfo ffmpeg

uwsgi.yaml changes needed in linux:
* wrap uwsgi.logformat in double quotes
* add `uwsgi.plugin: python3`
* add `pythonpath: /home/sosh/mspec/.venv/lib/python3.12/site-packages`

digital ocean notes
* load balancer
	* proxy mode --> disabled