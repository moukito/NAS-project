import parser
import writer
from GNS3 import Connector
from saveFile import write_string_to_file
from time import sleep


def main():
    (les_as, les_routers) = parser.parse_intent_file("format/exemple.json")

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
        router.set_interface_configuration_data(as_dico, router_dico)
    for router in les_routers:
        router.create_missing_links(as_dico, router_dico, connector)
    for router in les_routers:
        router.set_bgp_config_data(as_dico, router_dico)

        # Get the path for the router's config file
        try:
            router_config_path = connector.get_router_config_path(router.hostname)

            config_data = writer.get_final_config_string(as_dico[router.AS_number], router)

            # Write the config data to the file
            write_string_to_file(router_config_path, config_data)
            print(f"Configuration for {router.hostname} written to {router_config_path}.")
        except (ValueError, FileNotFoundError) as e:
            print(f"Error processing {router.hostname}: {e}")


if __name__ == "__main__":
    main()
