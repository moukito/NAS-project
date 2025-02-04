import sys
import threading

import parser
import writer
from GNS3 import Connector
from saveFile import write_string_to_file


def apply_router_configuration(connector, router, config_data, mode):
	"""
	Apply router configurations either by writing a .cfg file or using telnet.

	:param connector: Connector instance to interact with GNS3 or files.
	:param router: The router object to configure.
	:param config_data: The router configuration data as a string.
	:param mode: Mode of applying configuration ('cfg' or 'telnet').
	"""
	if mode == 'cfg':
		# Write configuration to .cfg file
		try:
			router_config_path = connector.get_router_config_path(router.hostname)
			write_string_to_file(router_config_path, config_data)
			print(f"Configuration for {router.hostname} written to {router_config_path}.")
		except (ValueError, FileNotFoundError) as e:
			print(f"Error processing {router.hostname}: {e}")
	elif mode == 'telnet':
		print(config_data)
		# Send configuration using telnet
		try:
			connector.send_commands_to_node(config_data, router.hostname)  # Send commands to the router
			connector.close_telnet_connection(router.hostname)
			print(f"Configuration for {router.hostname} applied via Telnet.")
		except (RuntimeError, ConnectionError) as e:
			print(f"Error applying configuration to {router.hostname}: {e}")
	else:
		print(f"Invalid mode '{mode}' specified. Skipping configuration for {router.hostname}.")


def main(mode, file):
	(les_as, les_routers) = parser.parse_intent_file(file)

	# Instantiating the Connector to manage configurations
	connector = Connector()  # Assuming project name "nap" with the Connector class

	as_dico = parser.as_list_into_as_number_dictionary(les_as)
	router_dico = parser.router_list_into_hostname_dictionary(les_routers)

	# Iterate over routers and create config files
	for router in les_routers:
		router.create_router_if_missing(connector)
		router.update_router_position(connector)
	for router in les_routers:
		# Generate the router configuration
		router.cleanup_used_interfaces(as_dico, router_dico, connector)
		router.set_interface_configuration_data(as_dico, router_dico, mode)
	for router in les_routers:
		router.set_loopback_configuration_data(as_dico, router_dico, mode)
		router.create_missing_links(as_dico, router_dico, connector)

	threads = {router.hostname: threading.Thread() for router in les_routers}
	config_data = {router.hostname: "" for router in les_routers}
	for router in les_routers:
		router.set_bgp_config_data(as_dico, router_dico, mode)

		# Get the path for the router's config file
		try:
			config_data[router.hostname] = writer.get_final_config_string(as_dico[router.AS_number], router, mode)

			if mode == 'telnet':
				connector.start_node(router.hostname)
				threads[router.hostname] = threading.Thread(
					target=connector.telnet_connection,
					args=(router.hostname,),
					daemon=True
				)
				threads[router.hostname].start()

		except (ValueError, FileNotFoundError) as e:
			print(f"Error creating configuration for {router.hostname}: {e}")
	for router in les_routers:
		try:
			threads[router.hostname].join()
			apply_router_configuration(connector, router, config_data[router.hostname], mode)
		except (ValueError, FileNotFoundError) as e:
			print(f"Error applying configuration for {router.hostname}: {e}")


if __name__ == "__main__":
	args_cons = sys.argv
	if len(args_cons) == 2:
		mode = str(args_cons[1])
		file = "format/full_infra.json"
	elif len(args_cons) == 3:
		mode = str(args_cons[1])
		file = str(args_cons[2])
	else:
		mode = input("Enter mode (cfg/telnet): ").strip().lower()
		file = "format/full_infra.json"
	if mode not in ["cfg", "telnet"]:
		print("Invalid mode specified. Please use 'cfg' or 'telnet'.")
		exit(1)
	main(mode, file)
