# servo-gitops
Optune servo adjust driver for GitOps

Note: this driver requires the `adjust.py` base class from the Optune servo core. It can be copied or symlinked here as part of packaging.  A servo using this driver also requires:

* 3rd party Python3 packages:  `ruamel.yaml` (required by this driver) and `requests` (required by the servo core).  When building a servo image, install these packages using pip3, e.g.:  `pip3 install ruamel.yaml requests`
* git and ssh client packages:  on debian based systems these may be installed with:  `apt-get install -y --no-install-recommends git openssh-client`

## overview

The GitOps adjust driver makes changes to YAML descriptors in a git repository in order to adjust settings of an application being optimized.  For example, a cpu resource allocation setting value received from the Optune service may be used to update the cpu resource limit for a pod in the YAML descriptor of a Kubernetes deployment in a github repository.  This driver does not directly handle the deployment of changes to such software infrastructure descriptors.  It does, however, provide pre- and post- adjust configuration for executing a shell command.  These commands may be used to effect, or verify the successfull completion of, the deployment of descriptor changes.

## servo configuration

A servo which uses this measure driver requires a private key (a deploy key) which provides read and write access to the desired git repository.  This key must be provided on the servo as `/root/.ssh/id_rsa` owned by root and mode 0600.  This key is used to authenticate via ssh when executing git commands.

See the following example for creating a Kubernetes configmap for this purpose.

Create a configmap in namespace `abc` using kubectl:
```
kubectl -n abc create configmap gitops-deploy-key --from-file=<my_id_rsa_file>
```

Configure the servo k8s deployment YAML descriptor:
```
spec:
  template:
    spec:
      volumes:
      - name: deploykey
        configMap:
          name: gitops-deploy-key
          defaultMode: 384  # decimal conversion of octal 0600
      containers:
      -name main
        ...
        volumeMounts:
        - name: deploykey
          mountPath: /root/.ssh/id_rsa
          subPath: id_rsa
          readOnly: true
```

## driver configuration

All configuration is provided to this driver through a YAML descriptor `config.yaml` to be provided in the same directory as the driver on the servo itself.  Here is an example of such a configuration file:

```
gitops:
    git_url:     ssh://git@github.com/<user>/<repository_name>.git
    git_branch:  <branch_name>

    # as required, configure pre- and post- adjust shell commands, e.g.:
    # post_cmd:  <cmd_or_script_to_verify_changes_are_deployed>

    components:
        c1:
            git_file:  deployments/c1.yaml
            settings:
                cpu:
                    key_path:  ['spec', 'template', 'spec', 'containers', 0, 'resources', 'limits', 'cpu']
                    min:       0.1
                    max:       3.0
                    type:      range
            dependencies:
                memory:
                    key_path: ['spec', 'template', 'spec', 'containers', 0, 'resources', 'limits', 'memory']
                    formula:  "str(300 + (cpu * 10)) + 'Mi'"
```

The `config.yaml` descriptor supports the following configuration:

* `git_url`:  ssh URL of git repository to clone for operations.  Required.
* `git_branch`:  git repository branch name.  Optional.
* `pre_cmd`:  Bash shell command to execute prior to adjust.  This optional command may be a string or a list.
* `post_cmd`:  Bash shell command to execute after measurement.  This optional command may be a string or a list.
* `pre_cmd_tout`:  optional timeout in seconds for `pre_cmd`.
* `post_cmd_tout`:  optional timeout in seconds for `post_cmd`.

Each named (e.g., `c1` in the example above) component of the `components` section of `config.yaml` supports the following configuration:

* `git_file`:  the file path, relative to the root of the git repository, of the YAML descriptor to modify when adjusting this component.  Required.

Each named (e.g., `cpu` in the example above) setting in the `settings` section of a component supports the following configuration:

* `key_path`:  a list of keys which specify the location of the value to be changed within the YAML descriptor `git_file`.  Required.
* `min`:  an optional minimum value for the setting.
* `max`:  an optional maximum value for the setting.
* `type`:  an optional setting type.  Default `range`.
* `val_conv`:  an optional conversion for setting values which are numbers (represented as floats for the purpose of optimization).  Valid values are any of `int` (convert to integer), `str` (convert to string) or `str_int` (convert to integer, then to string).  When propagating a setting value change to a YAML descriptor, the value is converted as indicated before output to YAML.

Any component may include an optional `dependencies` section.  This section specifies any number of additional changes to make to the YAML descriptor based on the changes to values of settings.  Each such dependent change is named (e.g., `memory` in the example above) and supports the following configuration:

* `key_path`:  a list of keys which specify the location of the value to be changed within the YAML descriptor `git_file`.
* `formula`:  a string containing Python code to be evaluated to produce the value to be set on `key_path`.  This formula may reference setting values by setting name (e.g., `cpu` in this example), and make use of a limited set of Python builtins, math functions/constants, and the str() function.
