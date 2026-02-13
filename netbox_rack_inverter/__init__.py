"""
Netbox Rack Inverter

Plugin configuration for Netbox Rack Inverter.

For a complete list of PluginConfig attributes, see:
https://docs.netbox.dev/en/stable/plugins/development/#pluginconfig-attributes
"""

__author__ = """Sam Richardson"""
__email__ = "srwfsec@proton.me"
__version__ = "0.1.2"


from netbox.plugins import PluginConfig


class Rack_InverterConfig(PluginConfig):
    name = "netbox_rack_inverter"
    verbose_name = "Netbox Rack Inverter"
    description = "Maintains physical position while changing rack order"
    author = "Sam Richardson"
    author_email = "srwfsec@proton.me"
    version = __version__
    base_url = "netbox_rack_inverter"
    min_version = "4.5.0"
    max_version = "4.5.99"


config = Rack_InverterConfig
