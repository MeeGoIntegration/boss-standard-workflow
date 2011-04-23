%define name boss-participant-prechecks
%define version 0.1.0
%define release 1

Summary: Prechecks BOSS SkyNet participant
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Islam Amer <islam.amer@nokia.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-participant-prechecks

Requires: python >= 2.5
Requires: python-boss-skynet
Requires: python-buildservice
Requires(post): boss-skynet

%description
Prechecks BOSS Skynet participant

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install


%post
if [ $1 -eq 1 ] ; then
    for i in already_testing has_changes package_complete package_successful \
        spec_valid target_repo ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/share/boss-skynet/*.py
