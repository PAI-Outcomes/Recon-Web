
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
($prog, $dir, $ext) = fileparse($0, '\..*');

&readsetCookies;
&readPharmacies;

if ( $USER ) {
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    &ReconRxAggregatedHeaderBlock_New;
  }
  else { 
    &ReconRxHeaderBlock;
  }
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;
   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);

$Pharmacy_Name = $Pharmacy_Names{$PH_ID};

$ntitle = "Contact Us for Assistance";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayContactUs;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayContactUs {
  print qq#<!-- displayContactUs -->\n#;

  print qq#Thank you $Pharmacy_Name for choosing ReconRx.<br>\n#;
  print qq#We are here to assist you.<br><br>\n#;

  print qq#<table>\n#;
  $URL = qq#mailto:RECON\@Outcomes.com\?subject=Recon-Rx pages - Contact Us email from $Pharmacy_Name#;

  print qq#<tr><th>Toll Free:</th> <td>(888) 255-6526</td></tr>\n#;
# print qq#<tr><th>Phone:</th>     <td>(913) 897-4343</td></tr>\n#;

  print qq#<tr><th>Email:</th>     <td><a href="$URL">RECON\@Outcomes.com</a></td></tr>\n#;
  print qq#<tr><th>Fax (General):</th> <td>(888) 618-8535</td></tr>\n#;
  print qq#<tr><th>Fax for<br>Check Posting:</th>       <td>(888) 255-6706</td></tr>\n#;
  print qq#</table>\n#;

  print qq#<br />\n#;
  print qq#<table width="600px">\n#;
  print qq#<tr><td colspan=2><h2>Regular Business Hours</h2></td></tr>\n#;
  print qq#<tr><td>Mon-Fri</td><td>8:00am - 5:00pm CST</td></tr>\n#;
  print qq#<tr><td>Sat-Sun</td><td>Closed</td></tr>\n#;
  print qq#<tr><td colspan=2><h2>Closed on the following holidays:</h2></td><tr>\n#;
  print qq#<tr><td colspan=2><i>Memorial Day, Independence Day, Labor Day, Veterans Day,  Thanksgiving Day, Day After Thanksgiving, Christmas Eve, Christmas Day, New Year's Eve, and New Year's Day</i></td></tr>\n#;
  print qq#</table>\n#;
}

#______________________________________________________________________________
