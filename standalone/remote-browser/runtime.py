"""Explicit Docker allowlist and resources, scoped exclusively to this service."""
import asyncio
import json
import re
from uuid import uuid4
from pathlib import Path
from aiohttp import ClientSession,ClientTimeout


class CapacityError(RuntimeError):pass


class Runtime:
    def __init__(self,config):
        self.config=config;self.label='remote-browser.installation='+config['installation']
        self.prefix='rbro-'+config['installation'][:8]+'-';self.egress=self.prefix+'egress'
        for image in (config['browser_image'],config['egress_image']):
            if not re.fullmatch(r'(?:[a-z0-9./_-]+@)?sha256:[a-f0-9]{64}',image):raise ValueError('Immutable image required')

    async def command(self,*args,check=True):
        process=await asyncio.create_subprocess_exec('docker','--host='+self.config.get('docker_socket','unix:///var/run/docker.sock'),*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        try:out,err=await asyncio.wait_for(process.communicate(),40)
        except BaseException:
            process.kill();await process.wait();raise
        if check and process.returncode:raise RuntimeError('Browser container operation failed')
        return out.decode().strip()

    async def recover(self):
        ids=await self.command('ps','-aq','--filter','label='+self.label)
        if ids:await self.command('rm','-fv',*ids.split())
        networks=await self.command('network','ls','-q','--filter','label='+self.label)
        if networks:await self.command('network','rm',*networks.split(),check=False)
        await self.command('network','create','--label',self.label,self.egress)

    async def launch(self,user):
        available=next((int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:')),0)
        if available<2200*1024:raise CapacityError('Not enough free memory to start the browser safely')
        key=self.prefix+uuid4().hex[:12];browser=key+'-chrome';proxy=key+'-proxy';network=key+'-net'
        result={'browser':browser,'proxy':proxy,'network':network,'port':None}
        try:
            await self.command('network','create','--internal','--opt','com.docker.network.bridge.gateway_mode_ipv4=isolated','--label',self.label,network)
            await self.command('run','-d','--pull=never','--name',proxy,'--label',self.label,'--network',self.egress,'--publish','127.0.0.1::8080',
                '--memory','96m','--memory-swap','96m','--cpus','0.25','--cpu-shares','64','--pids-limit','64','--read-only','--user','1000:1000','--cap-drop','ALL','--security-opt','no-new-privileges:true',
                '--log-driver','none','--tmpfs','/tmp:rw,nosuid,nodev,size=16m','--env','DENY_ALL_EGRESS='+('1' if self.config.get('deny_all_egress') else '0'),'--env','BROWSER_HOST='+browser,'--env','DENY_HOST='+self.config['hostname'],self.config['egress_image'])
            await self.command('network','connect','--alias','egress',network,proxy)
            flags='about:blank --proxy-server=http://egress:3128 --proxy-bypass-list=<-loopback> --disable-quic --force-webrtc-ip-handling-policy=disable_non_proxied_udp --disable-background-networking --disk-cache-size=33554432 --media-cache-size=16777216'
            await self.command('run','-d','--pull=never','--name',browser,'--label',self.label,'--label','remote-browser.user='+user,'--network',network,
                '--memory','1536m','--memory-swap','1536m','--cpus','1.0','--cpu-shares','128','--pids-limit','512','--shm-size','256m','--cap-drop','ALL',
                '--cap-add','CHOWN','--cap-add','DAC_OVERRIDE','--cap-add','FOWNER','--cap-add','SETUID','--cap-add','SETGID','--cap-add','KILL','--security-opt','no-new-privileges:true',
                '--log-driver','none','--tmpfs','/config:rw,nosuid,nodev,size=256m,uid=1000,gid=1000',
                '--env','PUID=1000','--env','PGID=1000','--env','SUBFOLDER=/rb/desktop/','--env','HARDEN_DESKTOP=true','--env','HARDEN_OPENBOX=true',
                '--env','SELKIES_COMMAND_ENABLED=false|locked','--env','SELKIES_FILE_TRANSFERS=','--env','SELKIES_CLIPBOARD_ENABLED=false|locked',
                '--env','SELKIES_MANUAL_WIDTH=1280','--env','SELKIES_MANUAL_HEIGHT=720','--env','SELKIES_FRAMERATE=15-15','--env','SELKIES_VIDEO_BITRATE=2000-2000','--env','SELKIES_AUDIO_BITRATE=64000','--env','CHROME_CLI='+flags,self.config['browser_image'])
            ports=json.loads(await self.command('inspect','--format','{{json .NetworkSettings.Ports}}',proxy))
            mapping=ports.get('8080/tcp')
            if not mapping:raise RuntimeError('Browser proxy exited before readiness')
            result['port']=int(mapping[0]['HostPort'])
            async with ClientSession(timeout=ClientTimeout(total=3)) as client:
                for attempt in range(40):
                    try:
                        async with client.get('http://127.0.0.1:'+str(result['port'])+'/rb/desktop/api/health') as response:
                            if response.status==200:return result
                    except (OSError,asyncio.TimeoutError):pass
                    await asyncio.sleep(1)
            raise RuntimeError('Browser did not become ready')
        except BaseException:
            await asyncio.shield(self.stop(result));raise

    async def stop(self,session):
        for name in (session['browser'],session['proxy']):
            await self.command('rm','-fv',name,check=False)
        await self.command('network','rm',session['network'],check=False)
