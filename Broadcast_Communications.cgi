
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

$ntitle = "Broadcast Communications";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebPage;
&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;
  @broadcasts = ("Broadcasts");
 
  print qq#<table class="main">\n#;
  print qq#<tr><th class="align_left lj_blue_bb">Date</th> <th class="align_left lj_blue_bb">Document</th></tr>\n#;
 
  foreach $BC (sort @broadcasts) {
    my ($prog, $dir, $ext);
 
    $webpath = qq#/WebShare/$BC#;
    $dskpath = "D:/WWW/members.recon-rx.com/WebShare/$BC";
 
    (@files) = &readfiles($dskpath);
    foreach $filename (sort {"\L$b" cmp "\L$a"} @files) {
 
       next if ( $filename =~ /Thumbs.db|.swp$|\~$/i );
       my ($jdate, $rest) = split("_", $filename, 2);
 
       $jdate =~ s/\./-/g;
       if ( $rest ) {
         ($prog, $dir, $ext) = fileparse($rest, qr/\.[^.]*/ );
         $prog =~ s/BIN_PCN/BIN\/PCN/g;
       } 
       else {
         $prog  = $jdate;
         $jdate = $nbsp;
       }
       print qq#<tr>\n#;
       print qq#<td class="align_left text_lj_blue" nowrap><span class="notice-date">$jdate</span></td> #;
       print qq#<td nowrap><span class="notice-date"><a href="$webpath/$filename" target="_blank"><strong>$prog</strong> ($ext)</span></a></td>#;
       print qq#</tr>\n#;
    }
  }
  print qq#</table>\n#;
}

