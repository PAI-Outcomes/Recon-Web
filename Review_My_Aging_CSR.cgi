#______________________________________________________________________________
#
# Jay Herder
# Date: 06/25/2012
# Review_My_Aging.cgi
#______________________________________________________________________________
#
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output
#______________________________________________________________________________
#
my $start = time();
my ($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";
my $help = qq|\n\nExecute as "$prog " without debug, or add " -d" for debug|;
my $debug;
my $verbose;
$nbsp = "&nbsp;";
$blank = "&lt; blank &gt;";

#$uberdebug++;
if ($uberdebug) {
# $incdebug++;
  $debug++;
  $verbose++;
}
#####$dbitrace++;
#_____________________________________________________________________________________
#
# Create HTML to display results to browser.
#______________________________________________________________________________
#
$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$debug   = $in{'debug'}   if (!$debug);
$verbose = $in{'verbose'} if (!$verbose);

$USER       = $in{'USER'};
$PASS       = $in{'PASS'};
$RUSER      = $in{'RUSER'};
$RPASS      = $in{'RPASS'};
$VALID      = $in{'VALID'};
$isAdmin    = $in{'isAdmin'};
$CUSTOMERID = $in{'CUSTOMERID'};
$LTYPE      = $in{'LTYPE'};
$LDATEADDED = $in{'LDATEADDED'};
$inTPP      = $in{'inTPP'};
$inBIN      = $in{'inBIN'};
$inBINP     = $in{'inBINP'};
$SORT       = $in{'SORT'};
$OWNER      = $in{'OWNER'};
$OWNERPASS  = $in{'OWNERPASS'};

($USER)  = &StripJunk($USER);
($PASS)  = &StripJunk($PASS);
($RUSER) = &StripJunk($RUSER);
($RPASS) = &StripJunk($RPASS);
($inTPP) = &StripJunk($inTPP);
($inBIN) = &StripJunk($inBIN);
($inBINP)= &StripJunk($inBINP);

$debug++ if ( $verbose );
$in{'debug'}++    if ( $debug );
$in{'verbose'}++  if ( $verbose );
$in{'incdebug'}++ if ( $incdebug );
#
my $submitvalue = "SAVE";
$CUSTOMERID = "" if ( !$CUSTOMERID );

#______________________________________________________________________________

&readsetCookies;

if ( $USER ) {
   $inNCPDP   = $USER;
   $dispNCPDP = $USER;
} else {
   $inNCPDP   = $in{'inNCPDP'};
   $dispNCPDP = $in{'dispNCPDP'};
}
if ( $PASS ) {
   $inNPI   = $PASS;
   $dispNPI = $PASS;
} else {
   $inNPI   = $in{'inNPI'};
   $dispNPI = $in{'dispNPI'};
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
$TODAY  = sprintf("%04d02d02d000000", $year, $month, $day);

$RUSER = $USER if ( $RUSER =~ /^\s*$/ );

#______________________________________________________________________________

($isMember, $VALID) = &isReconRxMember($USER, $PASS);

# print qq#USER: $USER, PASS: $PASS, VALID: $VALID, isMember: $isMember\n# if ($debug);

if ( $isMember && $VALID ) {

   &MyReconRxHeader;
   &ReconRxHeaderBlock;

} else {

#  &ReconRxHeaderBlock("No Side Nav");
#  &ReconRxMembersLogin;
   &ReconRxGotoNewLogin;

   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;
   exit(0);
}

#______________________________________________________________________________

# jlh. 08/02/2016. Don't overwrite the "ENV" variable, but use "LOCENV" for testing 
($LOCENV) = &What_Env_am_I_in;
####$LOCENV = "DONTDO";	# override to remove from development when not needed
# print "LOCENV: $LOCENV<br>\n";

if ( $LOCENV =~ /Dev/i ) {
  print "<i>*** For 'Total', now using dbTotalAmountPaid_Remaining instead of dbTotalAmountPaid ***</i><br>\n";
}

print "\nProg: $prog &nbsp; &nbsp; \nDate: $tdate &nbsp; Time: $ttime<P>\n" if ($debug);
print "In DEBUG   mode<br>\n" if ($debug);
print "In VERBOSE mode<br>\n" if ($verbose);
print "cookie_server: $cookie_server<br>\n" if ($debug);

if ( $debug ) {
   print "dol0: $0<br>\n";
   print "prog: $prog, dir: $dir, ext: $ext<br>\n" if ($verbose);
   print "<hr size=4 noshade color=blue>\n";
   print "PROG: $PROG<br>\n";
   print "<br>\n";
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
   my $key;
   foreach $key (sort keys %in) {
      print "key: $key, val: $in{$key}<br>\n";
   }
   print "JJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJJ<br>\n";
#  print "inNPI: $inNPI, dispNPI: $dispNPI<br>\n";
#  print "inNCPDP: $inNCPDP, dispNCPDP: $dispNCPDP<br>\n";
   print "<hr size=4 noshade color=blue>\n";
}

&readPharmacies;
&readThirdPartyPayers;
&readTPPPriSec;
&readReconExceptionRouting;

$dbin    = "RIDBNAME";  # Only database needed for this routine
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};
$FIELDS  = $DBFLDS{"$dbin"};
$FIELDS2 = $DBFLDS{"$dbin"} . "2";
$prefix  = "RI";	# unique to this table

# print "DBNAME: $DBNAME<hr>\n" if ($debug);

$FMT = "%0.02f";
my $TPP_Count = 0;
my $sixmonths = 6 * 30 * 24 * 60 * 60;

my %RParentkeys;
my %RBINs;
my %RTPP_Names;
my %RTotals;
my %RTotalPPs;
my %RF1to44s;
my %RF45to59s;
my %RF60to89s;
my %RFover90s;

my %Grand_RTotals;
my %Grand_RTotalPPs;
my %Grand_RF1to44s;
my %Grand_RF45to59s;
my %Grand_RF60to89s;
my %Grand_RFover90s;

#---------------------------------------
# Connect to the database

  $dbx = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
         { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
   
  DBI->trace(1) if ($dbitrace);
#---------------------------------------

if ( $inTPP ) {
   print qq#<a href="javascript:history.go(-1)"> Go Back</a><br>\n#;
   &displaySingleTPP($inTPP, $inBIN, $inBINP);
} else {
   $ntitle = "Aging Report";
   print qq#<h1 class="page_title">$ntitle</h1>\n#;
   &displayWebPage;
}

# Disconnect from database
$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

  print qq#<!-- displayWebPage -->\n#;
  print "sub displayWebPage: Entry.<br>\n" if ($debug);

  ($PROG = $prog) =~ s/_/ /g;
# print qq#<h2><i>In Work - $PROG</i></h2><br>\n#;

  my $found  =  0;
  my %JSTART = ();
  my %JEND   = ();

  $DateRanges{1} =  0;
  $DateRanges{2} = 45;
  $DateRanges{3} = 60;
  $DateRanges{4} = 90;

  foreach $DR (sort { $a <=> $b } keys %DateRanges) {
     $DRNext = $DR + 1;
     my $start;
     my $end;
     if ( $DR == 4 ) {
        $start = $DateRanges{$DR};
        $end   = $DateRanges{$DRNext} + 10000;

     } else {
        $start = $DateRanges{$DR};
        $end   = $DateRanges{$DRNext} - 1;
     }
     print "DR: $DR, start: $start, end: $end<br>\n" if ($debug);
     ($qstart, $qend) = &calcRanges($start, $end);
     $JSTART{$DR} = $qstart;
     $JEND{$DR}   = $qend;
     print "JSTART($DR): $JSTART{$DR}, JEND($DR): $JEND{$DR}<br>\n" if ( $verbose );
  }

###################################################################################
# Look for End_of_Fiscal_Year file
 
# print "ENV: $ENV, LOCENV: $LOCENV<br>\n";
  if ( $ENV =~ /Dev/i ) {
     $outdir    = qq#D:\\WWW\\www.recon-rx.com\\WebShare\\End_of_Fiscal_Year#;
  } else {
     $outdir    = qq#\\\\$PASRV3\\Webshare (ReconRx)\\End_of_Fiscal_Year#;
  }
# print "outdir: $outdir<br>\n";

  my $EOYfile  = "";
  my $EOYFNAME    = "";

# print "<hr>1. here<br>\n";
  opendir(DIR, "$outdir") or die $!;
# print "<hr>2. here<br>\n";
  while (my $fname = readdir(DIR)) {
# print "<hr>3. here<br>\n";
     # Use a regular expression to ignore fnames beginning with a period
#    print "Check file inNCPDP: $inNCPDP, fname: $fname<br>\n" if ($debug);
     next if ( $fname =~ m/^\./ );
     next if ( $fname !~ /${inNCPDP}_/ );

     $EOYfile  = "$outdir\\$fname";
     $mtime = (stat "$EOYfile")[9];
     if ( (time() - $mtime) <= $sixmonths ) {
        $EOYFNAME = $fname;
#       print "JJJ- $fname<br>\n" if ($debug);
     } else {
        $EOYfile = "";
        $EOYFNAME   = "";
     }
  }
  closedir(DIR);

# print "EOYfile: $EOYfile<br>mtime: $mtime<br><br>\n" if ($debug);

###################################################################################
# Look for End_of_Month file

  if ( $ENV =~ /Dev/i ) {
     $outdir    = qq#D:\\WWW\\www.recon-rx.com\\WebShare\\End_of_Month#;
  } else {
     $outdir    = qq#\\\\$PASRV3\\Webshare (ReconRx)\\End_of_Month#;
  }
# print "outdir: $outdir<br>\n";

  my $EOMfile  = "";
  my $EOMFNAME    = "";

  opendir(DIR, "$outdir") or die $!;
  while (my $fname = readdir(DIR)) {
     # Use a regular expression to ignore fnames beginning with a period
#    print "Check file inNCPDP: $inNCPDP, fname: $fname<br>\n" if ($debug);
     next if ( $fname =~ m/^\./ );
     next if ( $fname !~ /${inNCPDP}_/ );

     $EOMfile  = "$outdir\\$fname";
     $mtime = (stat "$EOMfile")[9];
     if ( (time() - $mtime) <= $sixmonths ) {
        $EOMFNAME = $fname;
#       print "JJJ- $fname<br>\n" if ($debug);
     } else {
        $EOMfile = "";
        $EOMFNAME   = "";
     }
  }
  closedir(DIR);

# print "EOMfile: $EOMfile<br>mtime: $mtime<br><br>\n" if ($debug);
###################################################################################

#-----------------------------------------------------------------------------------------------------
 
  &getData;

  $tableColumns =  6;
  $columnWidth  = 80;
  print qq#<table class="main">\n#;
# print qq#<tr><th class="align_left" colspan=$tableColumns><font size=+1>Aging Report</font></th></tr>\n#;

# - - - - -
# print "EOMfile: $EOMfile<br>\n";

  if ( $EOMfile !~ /^\s*$/ && -e "$EOMfile" ) {
     $webpath = "/Webshare/End_of_Month/$EOMFNAME";

    print qq#<tr valign=top><th colspan=2>
	<div style="padding: 5px; background: \#FFF; border: 1px solid \#CCC; border-radius: 10px;">
    <a href="/cgi-bin/Review_My_Aging_Monthly.cgi"><font color=red>End of Month Receivables</font></a>
    </div></th>#;

#    print qq#<tr valign=top><th colspan=2><font color=red>$nbsp</font><br></th>\n#;

  } else {
     print qq#<tr valign=top><th colspan=2>$nbsp</th>#;
  }

# - - - - -
# print "EOYfile: $EOYfile<br>\n";

  if ( $EOYfile !~ /^\s*$/ && -e "$EOYfile" ) {
     $webpath = "/Webshare/End_of_Fiscal_Year/$EOYFNAME";

    print qq#<tr valign=top><th colspan=2>
	<div style="padding: 5px; background: \#FFF; border: 1px solid \#CCC; border-radius: 10px;">
    <a href="$webpath"><font color=red>End of Fiscal Year Receivables</font></a>
    </div></th>#;

#    print qq#<tr valign=top><th colspan=2><font color=red>$nbsp</font><br></th>\n#;

  } else {
     print qq#<tr valign=top><th colspan=2>$nbsp</th>#;
  }
#
# - - - - -

  foreach $DR (sort { $a <=> $b } keys %DateRanges ) {
     my $start = substr($JSTART{$DR},4,2) . "/" . substr($JSTART{$DR},6,2) . "/" . substr($JSTART{$DR},0,4);
     my $end   = substr($JEND{$DR},4,2) . "/" . substr($JEND{$DR},6,2) . "/" . substr($JEND{$DR},0,4);
     if ( $DR == 4 ) {
        print qq#<th class="align_center"><font size=-1>$start<br>and<br>Older</font></th>#;
     } else {
        print qq#<th class="align_center"><font size=-1>$start thru $end</font></th>#;
     }
  }
# print "2. LOCENV: $LOCENV<br>\n";
  if ( $LOCENV =~ /Dev/i ) {
     $col1width = "width=250";
  } else {
     $col1width = "";
  }
  print qq#</tr>\n#;
  print qq#<tr>#;
  print qq#<th $col1width class="align_left">Third Party</th>#;
  print qq#<th class="align_right" bgcolor=yellow>Total OLD</th># if ($LOCENV =~ /Dev/i);
  print qq#<th class="align_right">Total</th>#;
  foreach $DR (sort { $a <=> $b } keys %DateRanges) {
     $DRNext = $DR + 1;
     $start = $DateRanges{$DR};
     $end   = $DateRanges{$DRNext} - 1;
     print "DR: $DR, start: $start, end: $end<br>\n" if ($debug);
     if ( !$start ) {
        print qq#<th class="align_right" width=$columnWidth>1-$end</th>#;
     } else {
        if ( $DR == 4 ) {
           print qq#<th class="align_right" width=$columnWidth>$DateRanges{$DR}+</th>#;
        } else {
           print qq#<th class="align_right" width=$columnWidth>$start-$end</th>#;
        }
     }
  }
  print qq#</tr>\n#;

  
  $row = 0;
  foreach $key ( sort { $RTPP_Names{$a} cmp $RTPP_Names{$b} } keys %RTPP_Names ) {
    $Parentkey = $RParentkeys{$key};
    $BIN       = $RBINs{$key};
    $TPP_Name  = $RTPP_Names{$key};
    $Total     = "\$" . &commify(sprintf("$FMT", $RTotals{$key}));
    $TotalPP   = "\$" . &commify(sprintf("$FMT", $RTotalPPs{$key}));
    $F1to44    = "\$" . &commify(sprintf("$FMT", $RF1to44s{$key}));
    $F45to59   = "\$" . &commify(sprintf("$FMT", $RF45to59s{$key}));
    $F60to89   = "\$" . &commify(sprintf("$FMT", $RF60to89s{$key}));
    $Fover90   = "\$" . &commify(sprintf("$FMT", $RFover90s{$key}));
	
    if (0 == $row % 2) {
      $rowclass = "";
    } else {
      $rowclass = "tan";
    }

#####
#   print "Total: $Total, TotalPP: $TotalPP<br>\n";
    my $addit = "";
    if ( $Total ne $TotalPP && $LOCENV =~ /Dev/i) {
       $addit = "*";
    }
#####

    print qq#<tr>#;
    print qq#<td class="$rowclass"><a href="${prog}.cgi?inTPP=${Parentkey}&inBIN=${BIN}&inBINP=${BIN}">$TPP_Name</a></td>#;

    print qq#<td align=right class="$rowclass">$Total $addit</td>#;
    print qq#<td align=right class="$rowclass">$TotalPP</td># if ($LOCENV =~ /Dev/i);
    print qq#<td align=right class="$rowclass">$F1to44</td>#;
    print qq#<td align=right class="$rowclass">$F45to59</td>#;
    print qq#<td align=right class="$rowclass">$F60to89</td>#;
    print qq#<td align=right class="$rowclass">$Fover90</td>#;
    print qq#</tr>\n#;
    $TPP_Count++;
	$row++;
  }

#-----------------------------------------------------------------------
# print "DATE RANGE NOT FOUND! - $OkeyDateTransmitted, $keyBinNumber, $jname, $keyTotalAmountPaid, $MyPrimary<br>\n" if ( !$found );

  print qq#</td></tr>\n# if ($debug);
  &displaySwitchData;
  print qq#</table>\n#;

  print qq#
  <p class="right">
    <img src="/images/spreadsheet.png" style="width: 32px; vertical-align: middle">
    <span style=""><a href="Review_My_Aging_Detailed.cgi">Create Detailed Aging File</a></span>
  </p>
  #;

  print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________

sub displaySwitchData {

# $debug++; $verbose++;

  print "<hr>sub displaySwitchData: Entry.<br>\n" if ( $debug );

  $savebin    =  0;
  $savekey    =  0;
  %slots      = ();

  $Grand_RTotals   = "\$" . &commify(sprintf("$FMT", $Grand_RTotals));
  $Grand_RTotalPPs = "\$" . &commify(sprintf("$FMT", $Grand_RTotalPPs));
  $Grand_RF1to44s  = "\$" . &commify(sprintf("$FMT", $Grand_RF1to44s));
  $Grand_RF45to59s = "\$" . &commify(sprintf("$FMT", $Grand_RF45to59s));
  $Grand_RF60to89s = "\$" . &commify(sprintf("$FMT", $Grand_RF60to89s));
  $Grand_RFover90s = "\$" . &commify(sprintf("$FMT", $Grand_RFover90s));

  print qq#<tr>#;
  print qq#<th class="green">Grand Totals</th>#;
  print qq#<th class="money" bgcolor=yellow>$Grand_RTotals</th># if ($LOCENV =~ /Dev/i);
  print qq#<th class="money">$Grand_RTotalPPs</th>#;
  print qq#<th class="money">$Grand_RF1to44s</th>#;
  print qq#<th class="money">$Grand_RF45to59s</th>#;
  print qq#<th class="money">$Grand_RF60to89s</th>#;
  print qq#<th class="money">$Grand_RFover90s</th>#;
  print qq#</tr>\n#;

  print "Lines printed: $TPP_Count<br>\n" if ($debug);
  if ( $TPP_Count <= 0 ) {
    print qq#<tr><th class="yellow" colspan=6>No Records found for $Pharmacy_Name</th></tr>#;
  }

  print "sub displaySwitchData: Exit. qstart: $qstart, qend: $qend<br>\n" if ( $debug );
  print "<hr size=4 color=red noshade>\n" if ( $debug );

}

#______________________________________________________________________________

sub displaySingleTPP {

  my ($inTPP, $inBIN, $inBINP) = @_;
  print "sub displaySingleTPP: Entry. inTPP: $inTPP, inBIN: $inBIN, inBINP: $inBINP<br>\n" if ($debug);

# print "RUSER: $RUSER, USER: $USER<hr>\n";

  my $juser = $RUSER || $USER;
 
#	&readSwitchData($juser);

#	  foreach $key (sort { $dbBinNumbers{$a} <=> $dbBinNumbers{$b} } keys %dbNCPDPNumbers) {
#	  
#	    $keyBinNumber = $dbBinParents{$key};
#	    $keyBinNumber =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces
#	    $lzBinNumber = substr("000000$keyBinNumber", -6);
#	    $TPP_ID = $Reverse_TPP_BINs{$lzBinNumber};
#	
#	#   print "JJJ: DB BIN: $dbBinNumbers{$key}, keyBinNumber: $keyBinNumber<br>\n" if ( $debug);
#	  
#	    ($keyPri, $MyPrimary) = &setMyPrimary($TPP_ID, $keyBinNumber);
#	#   print "($keyPri, $MyPrimary) = setMyPrimary($TPP_ID, $keyBinNumber)<br>\n" if ($debug);
#	    ($MyPriBin, $jname) = split("\-", $MyPrimary, 2);
#	    $MyPriBin =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces
#	  
#	    if ( $MyPriBin == $inBIN ) {
#	       print "setting dothese($keyPri)<br>\n" if ($verbose && !exists($dothese{$keyPri}) );
#	       $dothese{$keyPri}++;
#	    }
#	  }
#	  if      ( $SORT =~ /^NCPDP$/i ) {
#	    @sorted = sort { $dbNCPDPNumbers{$a} <=> $dbNCPDPNumbers{$b} } keys %dbNCPDPNumbers;
#	  } elsif ( $SORT =~ /^BIN$/i ) {
#	    @sorted = sort { $dbBinNumbers{$a} <=> $dbBinNumbers{$b} } keys %dbBinNumbers;
#	  } elsif ( $SORT =~ /^Rx$/i ) {
#	    @sorted = sort { $dbRxNumberExtendeds{$a} <=> $dbRxNumberExtendeds{$b} } keys %dbRxNumberExtendeds;
#	  } elsif ( $SORT =~ /^Filled/i ) {
#	    @sorted = sort { $dbDateOfServices{$a} cmp $dbDateOfServices{$b} } keys %dbDateOfServices;
#	  } elsif ( $SORT =~ /^Processed/i ) {
#	    @sorted = sort { $dbDateTransmitteds{$a} <=> $dbDateTransmitteds{$b} } keys %dbDateTransmitteds;
#	  } elsif ( $SORT =~ /^Amount/i ) {
#	    @sorted = sort { $dbTotalAmountPaid_Remainings{$a} <=> $dbTotalAmountPaid_Remainings{$b} } keys %dbTotalAmountPaid_Remainings;
#	  } elsif ( $SORT =~ /^Code/i ) {
#	    @sorted = sort { $dbCodes{$a} cmp $dbCodes{$b} } keys %dbCodes;
#	  } else {
#	    $SORT = "Rx";
#	    @sorted = sort { $dbRxNumberExtendeds{$a} <=> $dbRxNumberExtendeds{$b} } keys %dbRxNumberExtendeds;
#	  }

  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
  print qq#<INPUT TYPE="hidden" NAME="debug"   VALUE="$debug">\n#;
  print qq#<INPUT TYPE="hidden" NAME="verbose" VALUE="$verbose">\n#;
  print qq#<INPUT TYPE="hidden" NAME="db"      VALUE="$dbin">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inTPP"   VALUE="$inTPP">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inBIN"   VALUE="$inBIN">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inBINP"  VALUE="$inBINP">\n#;
  print qq#<INPUT TYPE="hidden" NAME="OWNER"   VALUE="$OWNER">\n#;
  print qq#<INPUT TYPE="hidden" NAME="OWNERPASS" VALUE="$OWNERPASS">\n#;

  print qq#<table class="main">\n#;
  my $out;
# $out = "$TPP_Names{ $Reverse_TPP_BINs{$inBINP} } ($inBINP)";
  $out = "BIN: $inBINP";

  my ($TPPsAss) = &associated_bins($inBINP);

  print qq#<tr><th colspan=6>\n#;
  print qq#    <div style="float:left;  text-align: left" >$out</div>\n#;
# print qq#    <div style="float:right; text-align: right">$Pharmacy_Name</div>\n#;
  print qq#</th></tr>\n#;
  print qq#<tr><th colspan=6>\n#;
  print qq#Associated Bins: $TPPsAss\n#;
  print qq#</th></tr>\n#;
  print qq#<tr><th colspan=6>#;
  print qq#    <div style="float:left;  text-align: left" ><font size=-1><i>Codes: NP-Non Payment, PP-Partial Payment</i></font></div>$nbsp\n#;
  print qq#    <div style="float:right; text-align: right"><font size=-1><i>Sorted by: $SORT</i></font></div>\n#;
  print qq#</th></tr>\n#;

  if ( $debug ) {
     print qq#<tr>#;
#    print qq#<td>dbNCPDPNumber</td># if ($debug);
     print qq#<td>dbBinNumber</td>#;
     print qq#<td>dbRxNumberExtended</td>#;
     print qq#<td>dbDateOfService</td>#;
     print qq#<td>dbDateTransmitted</td>#;
     print qq#<td>dbTotalAmountPaid_Remaining</td>#;
     print qq#<td>dbTotalAmountPaid</td>#;
     print qq#<td>dbCode</td>#;
     print qq#</tr>#;
  }
  print qq#<tr>#;
# print qq#<th><INPUT TYPE="Submit" NAME="SORT" VALUE="NCPDP"></th>#;
  print qq#<th><INPUT TYPE="Submit" NAME="SORT" VALUE="BIN"></th>#;
  print qq#<th><INPUT TYPE="Submit" NAME="SORT" VALUE="Rx"></th>#;
  print qq#<th><INPUT TYPE="Submit" NAME="SORT" VALUE="Filled Date"></th>#;
  print qq#<th><INPUT TYPE="Submit" NAME="SORT" VALUE="Processed Date"></th>#;
  print qq#<th style="text-align: right;"><INPUT TYPE="Submit" NAME="SORT" VALUE="Amount Due"></th>#;
  print qq#<th style="text-align: center;"><INPUT TYPE="Submit" NAME="SORT" VALUE="Code"></th>#;
  print qq#</tr>\n#;

  my $TotalPaid;
  my $TotalPaidPP;

#	  foreach $key (@sorted) {
#	
#	    ($keySwVendor, $keyDateTransmitted, $keyNCPDPNumber, $keyDateOfService, $keyRxNumberExtended, $keyRxNumber, $keyTransactionCode, $keyDateOfBirth, $keyTotalAmountPaid, $keyBinNumber) = split("##", $key);
#	
#	    next if ( $keyNCPDPNumber != $RUSER );
#	
#	    $keyBinNumber = $dbBinParents{$key};
#	    $keyBinNumber =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces
#	    $lzBinNumber = substr("000000$keyBinNumber", -6);
#	    $TPP_ID = $Reverse_TPP_BINs{$lzBinNumber};
#	 
#	    ($keyPri, $MyPrimary) = &setMyPrimary($TPP_ID, $keyBinNumber);
#	    print "($keyPri, $MyPrimary) = setMyPrimary($TPP_ID, $keyBinNumber)<br>\n" if ($debug);
#	
#	    my $continue = 0;
#	    foreach $chkkey (sort keys %dothese) {
#	       $continue++ if ( $keyPri == $chkkey );
#	    }
#	    next if ( !$continue );
#	
#	# have third party payer number. if this bin is a secondary, and it's parent it a -1, skip
#	    my $PriSec     = $TPP_PriSecs{$TPP_ID};
#	    my $TPP_Parent = $TPP_Parent_Name_Keys{$TPP_ID};
#	    next if ( $PriSec =~ /^Sec$/i && $MyPrimary == -1 );
#	    next if ( !$TPP_ID );
#	    print "$TPP_ID - $keyBinNumber- PriSec: $PriSec, TPP_Parent: $TPP_Parent<br>\n" if ($debug);
#	  
#	    $jbin = $dbBinNumbers{$key};
#	  
#	    print "jbin: $jbin, keyBinNumber: $keyBinNumber, TPP_ID: $TPP_ID<br>\n" if ($debug);
#	
#	    $Rx = $keyRxNumber;
#	
#	    my ($jyear)  = substr($dbDateOfServices{$key}, 0, 4);
#	    my ($jmonth) = substr($dbDateOfServices{$key}, 4, 2);
#	    my ($jday)   = substr($dbDateOfServices{$key}, 6, 2);
#	    my $jdate    = sprintf("%02d/%02d/%04d", $jmonth, $jday, $jyear);
#	
#	    my ($kyear)  = substr($keyDateTransmitted, 0, 4);
#	    my ($kmonth) = substr($keyDateTransmitted, 4, 2);
#	    my ($kday)   = substr($keyDateTransmitted, 6, 2);
#	    my $kdate    = sprintf("%02d/%02d/%04d", $kmonth, $kday, $kyear);
#	
#	    my $Paid     = "\$" . &commify(sprintf("$FMT", $keyTotalAmountPaid));
#	    $TotalPaid  += $keyTotalAmountPaid;
#	
#	    print qq#<tr>#;
#	#   print qq#<td>$keyNCPDPNumber</td>#;
#	
#	    print qq#<td>#, sprintf("%06d", $jbin), qq#</td>#;
#	#   print qq#<td>$jbin<br>$keyBinNumber</td>#;
#	
#	    print qq#<td>$Rx</td>#;
#	    print qq#<td>$jdate</td>#;
#	    print qq#<td>$kdate</td>#;
#	    print qq#<td class="align_right">$Paid</td>#;
#	    my $codeout = "";
#	    if ( $dbTCodes{$key} =~ /^\s*$/ ) {
#	       $codeout = $dbCodes{$key};
#	    } else {
#	       $codeout = $dbTCodes{$key};
#	    }
#	    print qq#<td class="align_center">$codeout</td>#;
#	    print qq#<td class="align_center">DBT: $dbTCodes{$key}<br>DBC: $dbCodes{$key}</td># if ($debug);
#	    print qq#</tr>\n#;
#	  }

# ------------------------ BEG. jlh. 01/06/2014. New code!

  if      ( $SORT =~ /^BIN$/i ) {
    $SORTFIELD = "dbBinNumber";
  } elsif ( $SORT =~ /^Rx$/i ) {
    $SORTFIELD = "dbRxNumber";
  } elsif ( $SORT =~ /^Filled/i ) {
    $SORTFIELD = "dbDateOfService";
  } elsif ( $SORT =~ /^Processed/i ) {
    $SORTFIELD = "dbDateTransmitted";
  } elsif ( $SORT =~ /^Amount/i ) {
    $SORTFIELD = "dbTotalAmountPaid_Remaining";
  } elsif ( $SORT =~ /^Code/i ) {
    $SORTFIELD = "dbCode";
  } else {
    $SORTFIELD = "dbRxNumber";
  }

  my $sql = "";

  $sql = qq#
SELECT dbBinNumber, dbRxNumber,
Date_Format(dbDateOfService,'%m/%d/%Y'),
Date_Format(dbDateTransmitted,'%m/%d/%Y'),
IFNULL(dbTotalAmountPaid_Remaining,0),
IFNULL(dbTotalAmountPaid,0),
dbCode
FROM $DBNAME.incomingtb
WHERE (1=1)
&& dbNCPDPNumber    = $juser
&& dbBinParentdbkey = $inTPP
&& dbCode<>"PD"
ORDER BY $SORTFIELD
#;

  print "<hr>sql:<br><pre>$sql</pre><hr>\n" if ($debug);

  $TotalPaidPP = 0;
  $TotalPaid   = 0;

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while (my @row = $sthrp->fetchrow_array()) {

    my ( $dbBinNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted,
         $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid,
         $dbCode ) = @row;

    next if ( $dbTotalAmountPaid == -20000);

#####
    if ( $dbTotalAmountPaid == $dbTotalAmountPaid_Remaining) {
       $addit = "";
    } else {
       $addit = "<br><font color=red>WAS: $dbTotalAmountPaid</font>";
    }
#####

    print qq#<tr>#;

    print qq#<td>#, sprintf("%06d", $dbBinNumber), qq#</td>#;
    print qq#<td>$dbRxNumber</td>#;
    print qq#<td>$dbDateOfService</td>#;
    print qq#<td>$dbDateTransmitted</td>#;
    print qq#<td class="align_right">\$$dbTotalAmountPaid_Remaining $addit</td>#;
    print qq#<td class="align_center">$dbCode</td>#;
    print qq#</tr>\n#;
    $TotalPaidPP += $dbTotalAmountPaid_Remaining;
    $TotalPaid   += $dbTotalAmountPaid;
     
  }

  $sthrp->finish;
 
# ------------------------ END. jlh. 01/06/2014. New code!


  $TotalPaidPP = "\$" . &commify(sprintf("$FMT", $TotalPaidPP));
  $TotalPaid   = "\$" . &commify(sprintf("$FMT", $TotalPaid));
  print qq#<tr>#;
  print qq#<th class="align_left yellow" colspan=4>Grand Totals</th>
           <th class="align_right yellow">$TotalPaidPP</th>
           <th class="align_right yellow">$TotalPaid</th>
           <th class="yellow">$nbsp</th>\n#;
 print qq#</tr>\n#;

  print qq#</table>\n#;

  print qq#</FORM>\n#;

  print "sub displaySingleTPP: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________

# my ($TPPsAss) = &associated_bins($inBINP);

sub associated_bins {

  my ($inBINP) = @_;
  my $TPPsAss  = "";
  my $BIN      = "";

# select Third_Party_Payer_Name from Third_Party_Payers WHERE Primary_Secondary='Pri' && BIN='$inBINP' ORDER BY Third_Party_Payer_Name;
  foreach $TPP_ID (sort { $TPP_Names{$a} cmp $TPP_Names{$b} } keys %TPP_Names) {
     next if ( $TPP_PriSecs{$TPP_ID} !~ /Pri/i );
     next if ( $TPP_BINs{$TPP_ID}    !~ /$inBINP/i );

#    print "1. TPP_ID: $TPP_ID, TPP_Names(): $TPP_Names{$TPP_ID}<br>\n";
     $TPPsAss .= "$TPP_Names{$TPP_ID}, ";
  }
#	  $TPPsAss =~ s/, $/<br>/g;
#	  foreach $BIN (sort keys %ExceptionBins) {
#	     # print "BIN: $BIN, inBINP: $inBINP, ExceptionBins(): $ExceptionBins{$BIN}<br>\n";
#	     if ( $ExceptionBins{$BIN} =~ /^$inBINP/ ) {
#	        my $val = $TPP_Names{$Reverse_TPP_BINs2{$BIN}};
#	        if ( $val !~ /^\s*$/ ) {
#	           $TPPsAss .= " $TPP_Names{$Reverse_TPP_BINs2{$BIN}}, ";
#	#          print "2. TPP_ID: $TPP_ID, Reverse_TPP_BINs2{$BIN} ( $TPP_Names{$Reverse_TPP_BINs2{$BIN}})<br>\n";
#	        }
#	     }
#	  }
  $TPPsAss =~ s/, $//g;

  return($TPPsAss);

}

#______________________________________________________________________________

sub getData {

  #Josh's Pharmacy = Buda Drug Store
# print "DBNAME: $DBNAME<br>\n";
  if ($inNCPDP =~ /1111111/ && $DBNAME =~ /ReconRxDB/i ) {
     $inNCPDP = 4540666;
  }

  my $sql = "";

  $sql = qq#
SELECT totals.dbBinParentdbkey, BIN, Third_Party_Payer_Name,
(IFNULL(TotalPP1to44,0) + IFNULL(TotalPP45to59,0) + IFNULL(TotalPP60to89,0) + IFNULL(TotalPPover90,0)) TotalPP,
Total, IFNULL(1to44,0) 1to44, IFNULL(45to59,0) 45to59, IFNULL(60to89,0) 60to89, IFNULL(over90,0) over90
FROM (
SELECT dbBinParentdbkey, BIN, Third_Party_Payer_Name, sum(dbTotalAmountPaid_Remaining) TotalPP, sum(dbTotalAmountPaid) Total
FROM $DBNAME.incomingtb 
LEFT JOIN (SELECT Third_Party_Payer_ID, Third_Party_Payer_Name, BIN, Reconcile
FROM officedb.third_party_payers) tpp 
ON dbBinParentdbkey = Third_Party_Payer_ID 
WHERE (1=1)
&& dbTotalAmountPaid != -20000
&& dbNCPDPNumber = $inNCPDP 
&& dbCode<>"PD"
&& tpp.Reconcile='Yes'
GROUP BY dbBinParentdbkey 
ORDER BY Third_Party_Payer_Name
) totals 

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid_Remaining) TotalPP1to44, sum(dbTotalAmountPaid_Remaining) 1to44
FROM $DBNAME.incomingtb 
WHERE (1=1)
&& dbTotalAmountPaid != -20000
&& dbNCPDPNumber = $inNCPDP
&& dbCode<>"PD"
&& (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 44 DAY) && DATE(dbDateTransmitted) <= CURDATE())
GROUP BY dbBinParentdbkey
) set_1to44
ON set_1to44.dbBinParentdbkey = totals.dbBinParentdbkey 

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid_Remaining) TotalPP45to59, sum(dbTotalAmountPaid) 45to59
FROM $DBNAME.incomingtb 
WHERE (1=1)
&& dbTotalAmountPaid != -20000
&& dbNCPDPNumber = $inNCPDP
&& dbCode<>"PD"
&& (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 59 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 45 DAY))
GROUP BY dbBinParentdbkey
) set_45to59
ON set_45to59.dbBinParentdbkey = totals.dbBinParentdbkey

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid_Remaining) TotalPP60to89, sum(dbTotalAmountPaid) 60to89
FROM $DBNAME.incomingtb 
WHERE (1=1)
&& dbTotalAmountPaid != -20000
&& dbNCPDPNumber = $inNCPDP
&& dbCode<>"PD"
&& (DATE(dbDateTransmitted) >= (CURDATE() - INTERVAL 89 DAY) && DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 60 DAY))
GROUP BY dbBinParentdbkey
) set_60to89
ON set_60to89.dbBinParentdbkey = totals.dbBinParentdbkey

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid_Remaining) TotalPPover90, sum(dbTotalAmountPaid) over90
FROM $DBNAME.incomingtb 
WHERE (1=1)
&& dbTotalAmountPaid != -20000
&& dbNCPDPNumber = $inNCPDP
&& dbCode<>"PD"
&& (DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 90 DAY))
GROUP BY dbBinParentdbkey
) set_over90 
ON set_over90.dbBinParentdbkey = totals.dbBinParentdbkey
#;

  print "<pre>sql:<br>$sql<br></pre>\n" if ($debug);

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while (my @row = $sthrp->fetchrow_array()) {

     my ($Parentkey, $BIN, $TPP_Name, $TotalPP, $Total, $F1to44, $F45to59, $F60to89, $Fover90) = @row;

     print qq#($Parentkey, $BIN, $TPP_Name, $Total, $F1to44, $F45to59, $F60to89, $Fover90)<br>\n# if ($debug);

     next if ( $Parentkey == -1 );	# jlh. 12/20/2013. For Tori!!!!

#    print "Parentkey: $Parentkey, dbBinParents(): $dbBinParents{$Parentkey}, 2: $dbBinParents{$BIN}<br>\n";
     my $keyBinNumber = $dbBinParents{$Parentkey} || $BIN;
     my $TPPID = $Reverse_TPP_BINs{$BIN};

     my ($keyPri, $MyPrimary) = &setMyPrimary($TPPID, $keyBinNumber);

     my ($jbin, $new_TPP_Name) = split("\-", $MyPrimary, 2);
     $TPP_Name     =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces
     $new_TPP_Name =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces

     if ("$TPP_Name" ne "$new_TPP_Name") {
#       my $debug++;
        print "(keyPri: $keyPri, MyPrimary: $MyPrimary, Parentkey: $Parentkey, BIN: $BIN)<br>\n" if ($debug);
        print qq#TPP_Name: $TPP_Name, New TPP_Name: $new_TPP_Name<hr>\n# if ($debug);
        $TPP_Name = $new_TPP_Name;
     }
#
#    $key = "$Parentkey##$BIN##$TPP_Name";
     $key = "$TPP_Name";
#    print "key: $key<br>\n";

     $RParentkeys{$key} = $Parentkey;
     $RBINs{$key}       = $BIN;
     $RTPP_Names{$key}  = $TPP_Name;
     $RTotals{$key}     += $Total;
     $RTotalPPs{$key}   += $TotalPP;
     $RF1to44s{$key}    += $F1to44;
     $RF45to59s{$key}   += $F45to59;
     $RF60to89s{$key}   += $F60to89;
     $RFover90s{$key}   += $Fover90;

     $Grand_RTotals     += $Total;
     $Grand_RTotalPPs   += $TotalPP;
     $Grand_RF1to44s    += $F1to44;
     $Grand_RF45to59s   += $F45to59;
     $Grand_RF60to89s   += $F60to89;
     $Grand_RFover90s   += $Fover90;

  }
  $sthrp->finish;
 
}

#______________________________________________________________________________
