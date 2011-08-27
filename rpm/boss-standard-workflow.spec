%define name boss-standard-workflow
%define version 0.0.1
%define release 1

Summary: Implement the BOSS standard workflow
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}_%{version}.orig.tar.gz
License: GPLv2+
Group: Development/Languages
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: David Greaves <david@dgreaves.com>
Url: http://meego.gitorious.org/meego-infrastructure-tools/boss-standard-workflow

Requires(post): boss-skynet

%description
This package provides the workflow definitions and tools to enable projects to use them.

%prep
%setup -q -n %{name}-%{version}

%build
make

%install
rm -rf $RPM_BUILD_ROOT
make DESTDIR=%{buildroot} install

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/srv/BOSS
/srv/BOSS/processes
/srv/BOSS/processes/StandardWorkflow
/srv/BOSS/processes/StandardWorkflow/BOSS_handle_SR
/srv/BOSS/processes/StandardWorkflow/trial_build_monitor
/usr/bin/swf_enable
