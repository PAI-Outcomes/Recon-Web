
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output

my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp;";

#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#

&readsetCookies;
&readPharmacies;

if ( $USER) {
 &MyReconRxHeader;
 &ReconRxHeaderBlock;
} 
else {

  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;

  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

$ntitle = "Weekly Remit Downloads Available";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebPage;
&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;
 
#  print qq#<table class="main">\n#;
#  print qq#<tr><th class="align_left lj_blue_bb">Date</th> <th class="align_left lj_blue_bb">Weekly Remit Downloads Available</th></tr>\n#;
 
  my ($prog, $dir, $ext);
 
  $webpath = qq#/WebShare/835s/$PH_ID/Weekly#;
  $dskpath = "D:/WWW/members.recon-rx.com/WebShare/835s/$PH_ID/Weekly";
 
  (@files) = &readfiles($dskpath);
  foreach $filename (sort {"\L$b" cmp "\L$a"} @files) {
 
     next if ( $filename =~ /Thumbs.db|.swp$|\~$/i );
#     my ($jdate, $rest) = split("", $filename, 2);
 
#     $jdate =~ s/\./-/g;

     print qq#<a href="$webpath/$filename" target="_blank">$filename</a></br>#;

#     print qq#<tr>\n#;
#     print qq#<td class="align_left text_lj_blue" nowrap><span class="notice-date">$filename - $jdate</span></td> #;
#     print qq#<td nowrap><span class="notice-date"><a href="$webpath/$filename" target="_blank"><strong>Download Remits</strong> (Zip)</span></a></td>#;
#     print qq#</tr>\n#;
  }
  print qq#</table>\n#;
}

