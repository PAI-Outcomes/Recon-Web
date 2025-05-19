require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1;
my $start = time();
my %EOMFNAMES = ();
my  $max  = 12;
my  $ymax = 2;
($prog, $dir, $ext) = fileparse($0, '\..*');

$title = "$prog";
$title = qq#${COMPANY} - $title# if ( $COMPANY );

&readsetCookies;
&login_rpt_ctl;

#______________________________________________________________________________

if ( $USER && $PH_ID ne "Aggregated") {
  &MyReconRxHeader;
  &ReconRxHeaderBlock;
} elsif ( $USER && $PH_ID eq "Aggregated") {
  $Agg  = '\\Aggregated';
  $Agg2 = '/Aggregated';
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

my $outdir    = qq#D:\\WWW\\members.recon-rx.com\\WebShare\\#;

#______________________________________________________________________________

$Pharmacy_Name = $Pharmacy_Names{$PH_ID};
$ntitle = " Copay Reports Menu";

print qq#<h3>$ntitle ( $LOGIN )</h3>\n#;

&get_EOM_AR;
&get_EOM_Reconciled;
&get_Ledger;
&get_EOY;

&displayAdminPage;
&MyReconRxTrailer;

exit(0);


sub get_EOY {
 $outdir    = qq#\\\\$WBSERVER\\Webshare (ReconRx)\\End_of_Fiscal_Year_Copay${testing}$Agg#;
  
#  print "outdir: $outdir\n";


  %EOYLfiles  = ();
  %EOYLFNAMES = ();
  %EOYRfiles  = ();
  %EOYRFNAMES = ();
  %dofiles    = ();
  @files      = ();

  opendir(DIR, "$outdir") or die $!;
  @files = grep(/\.xlsx$/,readdir(DIR));
  @files = grep(/_${USER}_/,@files);
  $file = @files;

  closedir(DIR);

  foreach $fname (@files) {
     my @pcs = split("_", $fname);
     my $ptr = @pcs;
        $ptr--;
     my $ptrM1 = $ptr -1 ;
     $pcs[$ptr] =~ s/\.xlsx//gi;
     my $threechar = substr($pcs[$ptr], 0, 3);

     next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
     next if ( $fname !~ /Reconciled_Claims_Summary_${USER}_/ );
   
     $ptrmonth = $months{$threechar};
     $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
     $dofiles{$key} = $fname;
  }

  foreach $key (sort { $b <=> $a } keys %dofiles) {

     $fname = $dofiles{$key};
     next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
     next if ( $fname !~ /Reconciled_Claims_Summary_${USER}_/ );

     print "fname: $fname<br>\n" if ( $debug );

     $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Fiscal_Year_Copay${testing}$Agg2/$fname";
     $thisfile       = "$outdir\\$fname";
     $EOYRfiles{$key} = "$webpath";

     $EOYRFNAMES{$key} = $fname;
  }

  $ptr = 0;
  %dofiles    = ();
  @files      = ();

  foreach $fname (@files) {
     my @pcs = split("_", $fname);
     my $ptr = @pcs;
        $ptr--;
     my $ptrM1 = $ptr -1 ;
     $pcs[$ptr] =~ s/\.xlsx//gi;
     my $threechar = substr($pcs[$ptr], 0, 3);

     next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
     next if ( $fname !~ /_Ledger_Report_${USER}_/ );
   
     $ptrmonth = $months{$threechar};
     $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
     $dofiles{$key} = $fname;
  }

  foreach $key (sort { $b <=> $a } keys %dofiles) {

     $fname = $dofiles{$key};
     next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
     next if ( $fname !~ /_Ledger_Report_${USER}_/ );

     print "fname: $fname<br>\n" if ( $debug );

     $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Fiscal_Year_Copay${testing}$Agg2/$fname";
     $thisfile       = "$outdir\\$fname";
     $EOYLfiles{$key} = "$webpath";

     $EOYLFNAMES{$key} = $fname;
  }

  $ptr = 0;

  print "sub displayWebPage: Exit.<br>\n" if ($debug);

}

sub get_EOM_AR {
  $outdir    = qq#\\\\$WBSERVER\\Webshare (ReconRx)\\End_of_Month_Copay${testing}$Agg#;
  
##  print "outdir: $outdir\n";


  %EOMfiles  = ();
  %EOMFNAMES = ();

  opendir(DIR, "$outdir") or die $!;
  @files = grep(/\.xlsx$/,readdir(DIR));
  @files = grep(/_${USER}_/,@files);
  $file = @files;

  closedir(DIR);

  foreach $fname (@files) {
    my @pcs = split("_", $fname);
    my $ptr = @pcs;
       $ptr--;
    my $ptrM1 = $ptr -1 ;
    $pcs[$ptr] =~ s/\.xlsx//gi;
    my $threechar = substr($pcs[$ptr], 0, 3);

    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /_${USER}_/ );
   
    $ptrmonth = $months{$threechar};
    $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
    $dofiles{$key} = $fname;
  }

  foreach $key (sort { $b <=> $a } keys %dofiles) {

    $fname = $dofiles{$key};
    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /_${USER}_/ );

    print "fname: $fname<br>\n" if ( $debug );

    $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Month_Copay${testing}$Agg2/$fname";
    $thisfile       = "$outdir\\$fname";
    $EOMfiles{$key} = "$webpath";
    $EOMFNAMES{$key} = $fname;
  }
  $ptr = 0;
  print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

sub get_Ledger {

 $outdir    = qq#\\\\$WBSERVER\\Webshare (ReconRx)\\End_of_Month_Copay_Ledger${testing}$Agg#;
  
#  print "outdir: $outdir\n";
  %EOMLfiles  = ();
  %EOMLFNAMES = ();
  %dofiles    = ();
  @files      = ();

  opendir(DIR, "$outdir") or die $!;
  @files = grep(/\.xlsx$/,readdir(DIR));
  @files = grep(/_${USER}_/,@files);
  $file = @files;

  closedir(DIR);

  foreach $fname (@files) {
    my @pcs = split("_", $fname);
    my $ptr = @pcs;
       $ptr--;
    my $ptrM1 = $ptr -1 ;
    $pcs[$ptr] =~ s/\.xlsx//gi;
    my $threechar = substr($pcs[$ptr], 0, 3);

    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /_${USER}_/ );
  
    $ptrmonth = $months{$threechar};
    $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
    $dofiles{$key} = $fname;
  }


  foreach $key (sort { $b <=> $a } keys %dofiles) {

    $fname = $dofiles{$key};
    print "fname: $fname<br>\n" if ( $debug );
    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /_${USER}_/ );

    $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Month_Copay_Ledger${testing}$Agg2/$fname";
    $thisfile       = "$outdir\\$fname";
    $EOMLfiles{$key} = "$webpath";

    $EOMLFNAMES{$key} = $fname;
  }

  $ptr = 0;
  print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

sub get_EOM_Reconciled {

 $outdir    = qq#\\\\$WBSERVER\\Webshare (ReconRx)\\End_of_Month_Copay_Reconciled_Claims${testing}$Agg#;
  
#  print "outdir: $outdir\n";
  %EOMRfiles  = ();
  %EOMRFNAMES = ();
  %dofiles    = ();
  @files      = ();
  opendir(DIR, "$outdir") or die $!;
  @files = grep(/\.xlsx$/,readdir(DIR));
  @files = grep(/_${USER}_/,@files);
  $file = @files;

  closedir(DIR);

  foreach $fname (@files) {
    my @pcs = split("_", $fname);
    my $ptr = @pcs;
       $ptr--;
    my $ptrM1 = $ptr -1 ;
    $pcs[$ptr] =~ s/\.xlsx//gi;
    my $threechar = substr($pcs[$ptr], 0, 3);

    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /_${USER}_/ );
  
    $ptrmonth = $months{$threechar};
    $key = sprintf("%04d%02d", $pcs[$ptrM1], $ptrmonth);
    $dofiles{$key} = $fname;
  }

  foreach $key (sort { $b <=> $a } keys %dofiles) {

    $fname = $dofiles{$key};
    print "fname: $fname<br>\n" if ( $debug );
    next if ( $fname =~ m/^\./ || $fname =~ m/^\.\./ );
    next if ( $fname !~ /_${USER}_/ );

    $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Month_Copay_Reconciled_Claims${testing}$Agg2/$fname";
    $thisfile       = "$outdir\\$fname";
    $EOMRfiles{$key} = "$webpath";

    $EOMRFNAMES{$key} = $fname;
  }

  $ptr = 0;
  print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

sub displayAdminPage {

  print qq#<!-- displayAdminPage -->\n#;
  print "sub displayAdminPage: Entry.<br>\n" if ($debug);

  my $Target = qq#target="_Blank"#;
  print qq#<table class='noborders' cellpadding=3 cellspacing=3 >\n#;

 ### Accounts Receivable 
    print qq#<tr><td>#;	
      print qq#<div class='CopayMenuDivs' >\n#;
      print qq# <div class='CopayDivHeader'>Copay Accounts Receivable</div>#;
      print qq# <ul class='CopayUL'>#;
      $v = keys %EOMFNAMES;
      if ($v <= 0) {
          print qq#<li><div>No End Of Month Files</div>\n#;
      }
      else {
        $ptr = 0;
        foreach $key (reverse sort keys %EOMFNAMES) {
          if ( $ptr < $max ) {
            print qq#<li><div><a href="$EOMfiles{$key}">$EOMFNAMES{$key}</a></div>\n#;
          }
          $ptr++;
        }
      }
        print qq#</ul></div>\n#; 
    print qq#</td>#;

 ###  Reconciled Claims
    print qq#<td>#;	
      print qq#<div class='CopayMenuDivs' >\n#;
      print qq# <div class='CopayDivHeader'>Copay Reconciled Claims</div>#;
      print qq# <ul class='CopayUL'>#;
      $v = keys %EOMRFNAMES;
      if ($v <= 0) {
       print qq#<li><div>No End Of Month Files</div>\n#;
      }
      else {
        $ptr = 0;
        foreach $key (reverse sort keys %EOMRFNAMES) {
          if ( $ptr < $max ) {
            print qq#<li><div><a href="$EOMRfiles{$key}">$EOMRFNAMES{$key}</a></div>\n#;
          }
          $ptr++;
        }
      }
      print qq#</ul></div>\n#; 
    print qq#</td></tr>#;

 ###Ledger
    print qq#<tr><td>#;   		
      print qq#<div class='CopayMenuDivs' >\n#;
      print qq# <div class='CopayDivHeader'>Copay Ledger</div>#;
      print qq# <ul class='CopayUL'>#;
       $v = keys %EOMLFNAMES;
        if ($v <= 0) {
            print qq#<li><div>No End Of Month Files</div>\n#;
        }
        else {
          $ptr = 0;
          foreach $key (reverse sort keys %EOMLFNAMES) {
            if ( $ptr < $max ) {
              print qq#<li><div><a href="$EOMLfiles{$key}">$EOMLFNAMES{$key}</a></div>\n#;
            }
            $ptr++;
          }
        }
      print qq#</ul></div>\n#; 
    print qq#</td><td>#;

 ### EOY Reports
      print qq#<div class='CopayMenuDivs' >\n#;
      print qq# <div class='CopayDivHeader'>Copay End Of Year Reports</div>#;
      print qq# <ul class='CopayUL'>#;
        $v = keys %EOYRFNAMES;
        if ($v <= 0) {
            print qq#<li><div>No End Of Year Reconciled Claims File</div>\n#;
        }
        else {
          $ptr = 0;
          foreach $key (reverse sort keys %EOYRFNAMES) {
            if ( $ptr < $ymax ) {
              print qq#<li><div><a href="$EOYRfiles{$key}">$EOYRFNAMES{$key}</a></div>\n#;
            }
            $ptr++;
          }
        }
        $ptr = 0;
        $v = keys %EOYLFNAMES;
        if ($v <= 0) {
            print qq#<li><div>No End Of Year Ledger File</div>\n#;
        }
        else {
          $ptr = 0;
          foreach $key (reverse sort keys %EOYLFNAMES) {
            if ( $ptr < $ymax ) {
              print qq#<li><div><a href="$EOYLfiles{$key}">$EOYLFNAMES{$key}</a></div>\n#;
            }
            $ptr++;
          }
        }
      print qq#</ul></div>\n#;	  
    print qq#</tr></td>#;	  
  print qq#</table>\n#;

  print "sub displayAdminPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________
