require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; 
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp\;";

$ret = &ReadParse(*in);
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

#______________________________________________________________________________

&readsetCookies;

#______________________________________________________________________________
#
if ( $USER ) {
   &MyReconRxHeader;
   &ReconRxHeaderBlock;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

  my $key;
  foreach $key (sort keys %in) {
     next if ( $key =~ /^PASS\s*$/ );	# skip printing out the password...
  }
  print "<hr size=4 noshade color=blue>\n";

($progname = $prog) =~ s/_/ /gi;
$ntitle = "<i>ReconRx $progname</i>";

print qq#<h3>$ntitle</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {
  print qq#<!-- displayAdminPage -->\n#;

  $actions{"Archive/Status Tool Searchable"} = "ADMIN_PCWNR_Archive_Status_Tool_Searchable.cgi";
  $actions{"Archive/Status Tool by Pharmacy"} = "ADMIN_PCWNR_Archive_Status_Tool_by_Pharmacy.cgi";

  $actionorder{"Archive/Status Tool Searchable"}  = 1;
  $actionorder{"Archive/Status Tool by Pharmacy"} = 2;

# print qq#<div id="textarea2" style="padding-bottom:40px;" class="notices">\n#;

  print qq#<table cellpadding=3 cellspacing=3 border=0>\n#;
  foreach $action ( sort {$actionorder{$a} <=> $actionorder{$b} } keys %actions ) {
     print qq#<tr> <td><a href="$actions{$action}">$action</a></td> </tr>\n#;
  }
  print qq#</table>\n#;

  print qq#      <li><i><font color=red>165 Pharmacies needed. Current: $ReconPharmaciesCount</font></i></a></li>\n# if ($ReconPharmaciesCount);
# print qq#</div>\n#;
# print qq#<!-- end  textarea2 --> \n#;
}

#______________________________________________________________________________
