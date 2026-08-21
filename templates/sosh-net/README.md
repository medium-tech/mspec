# mtech




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
1. ssh into server
1. `su sosh`
1. `cd /home/sosh/mspec`
1. `source .venv/bin/activate`
1. `git pull`
1. `pip install --upgrade mspec`
1. Check that `/home/sosh/mspec/.venv/lib/python3.12/site-packages/mspec/data/mapp-ui/src/markup.js` is the new version
1. `cd templates/sosh-net/`
1. `./server.sh restart`