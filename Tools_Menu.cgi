require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

&readsetCookies;

#______________________________________________________________________________

if ( $USER && $PH_ID ne "Aggregated") {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} elsif ( $USER && $PH_ID eq "Aggregated") {
  &MyReconRxHeader;
  &ReconRxAggregatedHeaderBlock_New;
} else {
   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);

#______________________________________________________________________________

$Pharmacy_Name = $Pharmacy_Names{$PH_ID};
$ntitle = " All Reports Menu";

print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&displayAdminPage;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayAdminPage {

  print qq#<!-- displayAdminPage -->\n#;
  print "sub displayAdminPage: Entry.<br>\n" if ($debug);

  my $Target = qq#target="_Blank"#;
  print qq#<table class='noborders' cellpadding=3 cellspacing=3 >\n#;
    print qq#<tr><td>#; 
      print qq#<div class='ReportMenuDivs'>\n#;
        print qq# <div class='ReportDivHeader'>Research</div>#;
          print qq# <ul class='ReportUL'>#;
            print qq# <li><div><a href="Search.cgi"$Target>Detailed Search</a></div> \n#;
            if ( $Pharmacy_Arete{$PH_ID} eq 'B') {
              print qq#<li><div><a href="Basic_Claim_Research_Tool.cgi"$Target>Outstanding Claims</a></div> \n#;
              print qq#<li><div><a href="Basic_Payment_Research_Tool.cgi"$Target>Missing Payment</a></div> \n#;
            }
        print qq#</ul></div>\n#;
    print qq#</td>#;

    print qq#<td>#;
      
      print qq#<div class='ReportMenuDivs'>\n#;
        print qq# <div class='ReportDivHeader'>Download</div>#;
        print qq# <ul class='ReportUL'>#;
		if ($PH_ID ne "Aggregated") {
          print qq# <li><div><a href="Bulk_835_Download.cgi"$Target>Weekly 835</a></div> \n#;
		}
        print qq#</ul></div>\n#;
        print qq#</div>\n#;
      print qq#</td></tr>#;

      print qq#<tr><td>#;
        print qq#<div class='ReportMenuDivs'>\n#;
          print qq# <div class='ReportDivHeader'>Training</div>#;
            print qq# <ul class='ReportUL'>#;
              print qq#<li><div><a href="Web_Training.cgi"$Target>ReconRx Demo</a></div> \n#;
            print qq#</ul></div>\n#;
          print qq#</div>\n#;
      print qq#</td>#;

##      if ( $ph_upload =~ /Yes/i ) {
        print qq#<td>#;
          print qq#<div class='ReportMenuDivs'>\n#;
            print qq# <div class='ReportDivHeader'>Upload</div>#;
              print qq# <ul class='ReportUL'>#;
			 if ($PH_ID ne "Aggregated") {
                print qq#   <li><div><a href="Upload835.cgi"$Target>Remittance</a></div> \n#;
			 }
              print qq#</ul></div>\n#;
            print qq#</div>\n#;
        print qq#</td></tr>#;
##      }

  print qq#</table>\n#;

  print "sub displayAdminPage: Exit.<br>\n" if ($debug);

}

