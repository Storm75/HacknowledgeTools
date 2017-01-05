#!/bin/bash

config()
{
    while true; do

        read -p "Do you want to configure the network? [Y/n]: " yn

        case $yn in

            [Nn]* ) return 1;;

            * )

                initInterfaceFile

                read -p "Enter default gateway : " routerip

                read -p "DNS (separated by spaces) : " nameservers
               
                bool_alias=false
                counter=0
                gatewayAndDnsNow=false 
                gatewayAndDnsSet=false

                for interface_name in $(ls /sys/class/net)

                do
                    ((counter=$counter+1))

                    while true; do

                        read -p "Configure the network interface $counter ($interface_name) ? [y/n]: " yn

                        case $yn in

                            [Yy]* )

                                while true; do

                                    read -p "Do you want to configure it using DHCP ? [y/n]: " yn

                                    case $yn in

                                        [Yy]* )
                                            bool_DHCP=true
                                            writeInterfaceFile
                                            bool_DHCP=false
                                            break;;

                                        [Nn]* )
                                                getinfo
                                                writeInterfaceFile
                                                break;;

                                        * ) echo "Please enter y or n!";;
                                    esac
                                done

                                alias_count=0

                                while true; do

                                    read -p "Do you want to add additional aliases for this interface ($interface_name) ? [y/n] : " yn

                                    case $yn in

                                        [Yy]* )
                                                bool_alias=true
                                                savename=$interface_name
                                                interface_name="$interface_name:$alias_count"
                                                getinfo
                                                writeInterfaceFile
                                                interface_name=$savename
                                                bool_alias=false
                                                ((alias_count=$alias_count+1))
                                            ;;

                                        [Nn]* ) break;;

                                        * ) echo "Please enter y or n!";;

                                    esac

                                done

                                break
                                ;;

                            [Nn]* ) break ;;

                        * ) echo "Please enter y or n!";;

                        esac

                    done

                done

            echo -e "\nYour informations were saved in '$file' file."

            return 0;;

        esac

    done

}

getinfo()
{
    if [ "$bool_alias" = true ] ; then
        search_iface=$(echo $interface_name |cut -d: -f1)
    else
        search_iface=$interface_name
    fi

    current_ip=$($ifconfig_path $search_iface |grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*'|grep -Eo '([0-9]*\.){3}[0-9]*')

    current_netmask=$($ifconfig_path $search_iface |grep -Eo 'netmask (addr:)?([0-9]*\.){3}[0-9]*'|grep -Eo '([0-9]*\.){3}[0-9]*')

    read -p "Enter $interface_name IP [$current_ip] : " if_staticip

    read -p "Enter $interface_name netmask [$current_netmask] : " if_netmask

    if [[ -z "${if_staticip// }" ]];
        then if_staticip=$current_ip
    fi

    if [[ -z "${if_netmask// }" ]];
        then if_netmask=$current_netmask
    fi
}

initInterfaceFile()
{

cat << EOF > $file

# This file describes the network interfaces available on your system

# and how to activate them. For more information, see interfaces(5).

# The loopback network interface

auto lo

iface lo inet loopback

EOF

}

writeInterfaceFile()
{
    if [ "$bool_alias" = false ] ;then
        
      if [ "$gatewayAndDnsSet" = false ] ;then

            while true; do

            read -p "Assign gateway and nameservers for this interface ? [y/n]: " yn

            case $yn in
                [Yy]* )
                    gatewayAndDnsSet=true
                    gatewayAndDnsNow=true
                    break;;
                [Nn]* )
                    break;;
            esac
          done
        fi
    fi

    config="auto $interface_name\niface $interface_name inet"
    if [ "$bool_DHCP" = true ] ;then

       config="$config dhcp\n"
    else
       config="$config static\n"
       config="$config \taddress $if_staticip\n\tnetmask $if_netmask\n"
       if [ "$gatewayAndDnsNow" = true ] ;then
         config="$config \tgateway $routerip\n"
       fi

    fi

    if [ "$bool_alias" = false ] ; then
       if [ "$gatewayAndDnsNow" = true ] ;then
         config="$config \tdns-nameservers $nameservers\n"
       fi
    fi

    if [ "$gatewayAndDnsNow" = true ] ;then
       gatewayAndDnsNow=false
    fi

    echo -e $config >> $file
}

ifconfig_path="/sbin/ifconfig"

file="/home/storm/Documents/SCRT/Hacknowledge/sondes/interfaces"

clear

config
