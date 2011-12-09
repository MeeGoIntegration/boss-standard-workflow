lang en_US.UTF-8
keyboard us
timezone --utc America/Los_Angeles
auth --useshadow --enablemd5
part / --size 2048 --ondisk sda --fstype=ext2
rootpw meego
# xconfig --startxonboot
bootloader --timeout=5
# desktop --autologinuser=meego  --defaultdesktop=DUI --session="/usr/bin/mcompositor"
user --name meego  --groups audio,video --password meego

repo --name=oss --baseurl=http://repo.meego.com/MeeGo/releases/1.2.0/repos/oss/ia32/packages/ --gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-meego

%packages  --excludedocs
@MeeGo Base

kernel
openssh
openssh-clients
openssh-server
eat-device

%end
%post

# save a little bit of space at least...
# rm -f /boot/initrd*

# make sure there aren't core files lying around
rm -f /core*

# Prelink can reduce boot time
if [ -x /usr/sbin/prelink ]; then
    /usr/sbin/prelink -aRqm
fi

# work around for poor key import UI in PackageKit
rm -f /var/lib/rpm/__db*
rpm --rebuilddb


echo > /boot/extlinux/extlinux.conf

cat << EOF >> /boot/extlinux/extlinux.conf

prompt 0
timeout 1

menu hidden
DEFAULT meego0

menu title Welcome to MeeGo!
label meego0
    menu label MeeGo
    kernel vmlinuz
    append ro root=/dev/vda1 vga=current
    menu default

EOF

%end

%post --nochroot
if [ -n "$IMG_NAME" ]; then
    echo "BUILD: $IMG_NAME" >> $INSTALL_ROOT/etc/meego-release
fi
%end
