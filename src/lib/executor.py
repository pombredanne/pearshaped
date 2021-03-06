import os
import subprocess
import shutil

__all__ = ["Executor"]

def out(msg):
    print(msg, flush=True)

class Docker():

    def __init__(self):
        self.committed = []

    def set_image(self, image):
        self.image = image

    def exec(self, command):
        out("docker " + command)
        return subprocess.Popen("docker " + command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                shell=True,
                universal_newlines=True)

    def check_output(self, command):
        return subprocess.check_output('docker ' + command,
                shell=True,
                universal_newlines=True)

    def run_image(self, cmd='', flags=''):
        script = "docker run %s -i %s %s" % (flags, self.image, cmd)
        out(script)
        return subprocess.Popen(
                script,
                stdin=subprocess.PIPE,
                shell=True,
                universal_newlines=True)

    def commit_current_to(self, new_image):
        """ save the current/last running container to an image """
        ps = self.exec("ps -lq")
        ps.wait()
        self.container = ps.stdout.read().strip()

        commit = self.exec("commit %s %s" % (self.container, new_image))
        commit.wait()
        if commit.returncode != 0:
            raise RuntimeError(commit.stdout)

        self.committed.append(new_image)
        self.image = new_image

    def remove_all_committed(self):
        for image in self.committed:
            subprocess.check_call(['docker', 'rmi', '-f', image])

class Executor():
    # uniquely identifies each built image during this session
    global_id = 1

    def __init__(self, host_repo_path, repo_dir, config):
        self.host_repo_path = host_repo_path
        self.repo_dir = repo_dir
        self.config = config
        self.build_id = self.global_id
        self.global_id += 1

        self.docker = Docker()

    def label(self):
        return "build" + str(self.build_id)

    def run(self):
        ConfigGuesser(self.config, self.repo_dir).fill_unwritten_steps()
        status  = self._build_sequence()

        if status != 'success':
            return False

        return True

    def _build_sequence(self):
        self.docker.set_image(self._toolchain_container())

        pre_steps = ['before_install', 'install', 'before_script']
        for name in pre_steps:
            errored = not self._execute_step(name)
            if errored:
                return 'errored'

        success = self._execute_step('script')

        if success:
            self._execute_step('after_success')
        else:
            self._execute_step('after_failure')

        self._execute_step('after_script')

        if success:
            self.docker.remove_all_committed()
            return 'success'
        else:
            return 'failure'

    def _execute_step(self, name):
        if name not in self.config:
            return True

        out("executing step %s" % name)

        env_flags = " ".join(["-e \"{}={}\"".format(key, value) for key,value in self.EXTRA_ENV.items()])
        print(env_flags)
        commands = self._config_as_list(name)

        script = self._script_preamble() + self._with_echo(commands)

        proc = self.docker.run_image(flags='-v \"{}\":/build {}'.format(self.host_repo_path, env_flags))
        proc.stdin.write(";\n".join(script))

        proc.stdin.close()
        proc.wait()

        if proc.returncode != 0:
            out("failed during '%s' step" % name)
            return False
        else:
            try:
                self.docker.commit_current_to("%s-%s" % (self.label(), name))
            except RuntimeError:
                out("failed to commit %s on step %s" % (self.docker.container, name))
                return False

        return True

    def _script_preamble(self):
        preamble = [
                '. /etc/profile.d/rvm.sh',
                'set -e'
                ]

        if 'rvm' in self.config:
            chosen_rvm =  self._config_as_list('rvm')[0]
            preamble += [
                    'rvm install ' + chosen_rvm,
                    'echo rvm use ' + chosen_rvm,
                    'rvm use ' + chosen_rvm,
                    'gem install bundler rake',
                    ]

        preamble.append('cd "%s"' % self.repo_dir)

        return preamble

    def _with_echo(self, cmd_list):
        cmds = []

        for cmd in cmd_list:
            cmds.append('echo ' + cmd)
            cmds.append(cmd)

        return cmds

    def _config_as_list(self, key):
        if isinstance(self.config[key], str):
            return [self.config[key]]
        else:
            return self.config[key]

    def _toolchain_container(self):
        if 'language' in self.config:
            language = self.config['language']
            label = 'orchard-language-' + language

            images_output = self.docker.check_output('images -q %s' % label)

            if len(images_output) > 0:
                return label
            else:
                out("warning: language %s not found. using base image" % language)

        return "orchard-base"

    EXTRA_ENV = {
        'CI': 'true',
        'TRAVIS': 'true',
        'CONTINUOUS_INTEGRATION': 'true',
        'DEBIAN_FRONTEND': 'noninteractive',
        'LANG': 'en_US.UTF-8',
        'RAILS_ENV': 'test',
        'RACK_ENV': 'test',
        'MERB_ENV': 'test',
        'JRUBY_OPTS': '--server -Dcext.enabled=false -Xcompile.invokedynamic=false'
    }


class ConfigGuesser():
    def __init__(self, config, repo_dir):
        self.config = config
        self.repo_dir = repo_dir

    def fill_unwritten_steps(self):
        if self.is_language('ruby'):
            bundle_install = 'bundle install --jobs=3 --retry=3'
            if 'install' not in self.config:
                if 'gemfile' in self.config:
                       self.config['install'] = [bundle_install + ' --gemfile=' + self._config_as_list('gemfile')[0]]
                elif os.path.exists(os.path.join(self.repo_dir, 'Gemfile.lock')):
                       self.config['install'] = [bundle_install + ' --deployment']
                elif os.path.exists(os.path.join(self.repo_dir, 'Gemfile')):
                       self.config['install'] = [bundle_install]

            if 'script' not in self.config:
                if os.path.exists(os.path.join(self.repo_dir, 'Rakefile')):
                       self.config['script'] = ['rake test']

        elif self.is_language('node_js'):
            if 'install' not in self.config:
                self.config['install'] = ['npm install']

            if 'script' not in self.config:
                self.config['script'] = ['npm test']

        elif self.is_language('python') or self.is_language('python3'):
            if 'install' not in self.config and os.path.exists(os.path.join(self.repo_dir, 'requirements.txt')):
                self.config['install'] = ['pip install -r requirements.txt']

    def is_language(self, lang):
       return self.config.get('language', None) == lang
