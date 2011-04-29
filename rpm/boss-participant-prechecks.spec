%define name boss-participant-prechecks
%define version 0.1.1
%define release 1

Summary: Prechecks BOSS SkyNet participant
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.tar.gz
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
        for i in \
            check_already_testing \
            check_has_valid_repo \
            check_multiple_destinations \
            check_no_changes \
            check_package_built_at_source \
            check_package_is_complete \
            check_spec \
            check_submitter_maintainer \
            get_submitter_email \
            check_has_relevant_changelog \
            check_is_from_devel \
        ; do

        skynet make_participant -n $i -p /usr/share/boss-skynet/$i.py

    done
fi

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/share/boss-skynet/*.py
