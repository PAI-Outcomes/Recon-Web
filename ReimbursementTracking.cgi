
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

my $Agg;
my $Agg2;

$| = 1; # don't buffer output
($prog, $dir, $ext) = fileparse($0, '\..*');

&readsetCookies;
&readPharmacies;


if ( $USER ) {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
  $ID = $Reverse_Pharmacy_NCPDPs{$inNCPDP};
} 
else {
  &ReconRxGotoNewLogin;
  &MyReconRxTrailer;
  print qq#</BODY>\n#;
  print qq#</HTML>\n#;
  exit(0);
}

($ENV) = &What_Env_am_I_in;

$ntitle = "Reimbursement Tracking for $inNCPDP";
print qq#<h1 class="page_title">$ntitle</h1>\n#;

&displayWebPage;
&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;

  if ( $ENV =~ /Dev/i ) {
  } else {
     $outdir    = qq#\\\\$WBSERVER\\Webshare (ReconRx)\\ReimbursementTracking#;
  }

  %EOMfiles  = ();
  %EOMFNAMES = ();

  opendir(DIR, "$outdir") or die $!;
  my @files = sort readdir(DIR);
  closedir(DIR);
  foreach $fname (@files) {
    my @pcs = split("_", $fname);
    my $ptr = @pcs;
    $ptr--;
    my $ptrM1 = $ptr -1 ;
    $pcs[$ptr] =~ s/\.xlsx//gi;
    my $threechar = substr($pcs[$ptr], 0, 3);

    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    if ( $PH_ID  ne 'Aggregated') {
      next if ( $fname !~ /${inNCPDP}_${ID}_/ ); 
    }
    else {
      next if ( $fname !~ /_${inNCPDP}_/ );
    }

    $ptrmonth = $months{$threechar};
    $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
    $dofiles{$key} = $fname;
  }

  foreach $key (sort { $b <=> $a } keys %dofiles) {

    $fname = $dofiles{$key};
    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /${inNCPDP}_/ );

    $webpath = "https://${ENV}.Recon-Rx.com/Webshare/ReimbursementTracking/$fname";
    $thisfile       = "$outdir\\$fname";
    $EOMfiles{$key} = "$webpath";
    $EOMFNAMES{$key} = $fname;
  }

  $ptr = 0;
  $max = 12;
  foreach $key (reverse sort keys %EOMFNAMES) {
    if ( $ptr < $max ) {
       print qq#<a href="$EOMfiles{$key}">$EOMFNAMES{$key}</a><br>\n#;
    }
    $ptr++;
  }
}
