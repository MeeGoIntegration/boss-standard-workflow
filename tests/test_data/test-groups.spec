%define name test-groups
%define version 0.1
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
Vendor: Vendor <vendor@example.com>

%description
This is a test package for the update_patterns unit tests.

%prep
%setup -q -c

%build

%install
rm -rf $RPM_BUILD_ROOT
install -d  $RPM_BUILD_ROOT/usr/share/patterns
install testpattern.xml $RPM_BUILD_ROOT/usr/share/patterns

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
/usr/share/patterns
