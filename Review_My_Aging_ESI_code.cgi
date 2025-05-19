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
$inTPPNme   = $in{'inTPPNme'};
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
my $disclaimer = 'star';
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
$CHECKYEAR = $year + 1;

$RUSER = $USER if ( $RUSER =~ /^\s*$/ );

#______________________________________________________________________________

($isMember, $VALID) = &isReconRxMember($USER, $PASS);


if ( $isMember && $VALID ) {

   &MyReconRxHeader;
   &ReconRxHeaderBlock;

} else {

   &ReconRxGotoNewLogin;
   &MyReconRxTrailer;

   print qq#</BODY>\n#;
   print qq#</HTML>\n#;

   exit(0);
}

#______________________________________________________________________________

# jlh. 08/02/2016. Don't overwrite the "ENV" variable, but use "LOCENV" for testing 
##($LOCENV) = &What_Env_am_I_in;

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
   print "<hr size=4 noshade color=blue>\n";
}

&readPharmacies;
&readThirdPartyPayers;
&readTPPPriSec;
&readReconExceptionRouting;
&readReconExceptionRouting2;

$dbin    = "RIDBNAME";  # Only database needed for this routine
$DBNAME  = $DBNAMES{"$dbin"};
$TABLE   = $DBTABN{"$dbin"};
$FIELDS  = $DBFLDS{"$dbin"};
$FIELDS2 = $DBFLDS{"$dbin"} . "2";
$prefix  = "RI";	# unique to this table

if ( $uberdebug ) {
  $DBNAME = "Testing";
}
print "DBNAME: $DBNAME<hr>\n" if ($debug);

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
   &displaySingleTPP($inTPP, $inBIN, $inBINP, $inTPPNme);
} else {
   if ( $inNCPDP =~ 1111111 ) {
      print qq!<div id="inline" style="font-size: 12px; color: #0099ff; padding: 30px; font-weight: bold;">Disclaimer: ReconRx cannot reconcile claims for Medicare Part B and select traditional state Medicaid plans.  ReconRx cannot provide complete reconciliation services for Express Scripts.</div>!;
   }   
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

  my $found       =  0;
  my %JSTART      = ();
  my %JEND        = ();

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
 
  if ( $ENV =~ /Dev/i ) {
     $outdir    = qq#D:\\WWW\\www.recon-rx.com\\WebShare\\End_of_Fiscal_Year#;
  } else {
     $outdir    = qq#\\\\$PASRV3\\Webshare (ReconRx)\\End_of_Fiscal_Year#;
  }
  print "outdir: $outdir<br>\n" if ($debug);

  my $EOYfile   = "";
  my $EOYFNAME  = "";
  my $savemtime =  0;
# CHECKYEAR set at top

  for ( $CKYEAR=$CHECKYEAR; $CKYEAR >= $CHECKYEAR-3; $CKYEAR-- ) {
     print "Trying CKYEAR: $CKYEAR<br>\n" if ($debug);

     opendir(DIR, "$outdir") or die $!;
     while (my $fname = readdir(DIR)) {
        # Use a regular expression to ignore fnames beginning with a period
   
        next if ( $fname =~ m/^\./ );
        next if ( $fname !~ /${inNCPDP}_${CKYEAR}/ );
   
        print "<hr>Check file inNCPDP: $inNCPDP<br>fname: $fname<br>\n" if ($debug);
   
        if ( $fname =~ /${inNCPDP}_${CKYEAR}/ ) {
           $found++;
           $EOYFNAME  = $fname;
           $EOYfile   = "$outdir\\$fname";
           $mtime     = (stat "$EOYfile")[9];
           $savemtime = $mtime;
           print "<font color=red>fname: $fname</font><br>\n" if ($debug);
        }
        last if ( $found);
     }
     closedir(DIR);
     last if ( $found);
  }

  if ( $debug ) {
     print "<hr>\n";
     print "savemtime: $savemtime<br>\n";
     print scalar localtime $savemtime, "<br>\n";
     print "EOYFNAME: $EOYFNAME<br>\n";
  }

###################################################################################
# Look for End_of_Month file

  if ( $ENV =~ /Dev/i ) {
     $outdir    = qq#D:\\WWW\\www.recon-rx.com\\WebShare\\End_of_Month#;
  } else {
     $outdir    = qq#\\\\$PASRV3\\Webshare (ReconRx)\\End_of_Month#;
  }

  my $EOMfile  = "";
  my $EOMFNAME    = "";

  opendir(DIR, "$outdir") or die $!;
  while (my $fname = readdir(DIR)) {
     next if ( $fname =~ m/^\./ );
     next if ( $fname !~ /${inNCPDP}_/ );

     $EOMfile  = "$outdir\\$fname";
     $mtime = (stat "$EOMfile")[9];
     if ( (time() - $mtime) <= $sixmonths ) {
        $EOMFNAME = $fname;
     } else {
        $EOMfile = "";
        $EOMFNAME   = "";
     }
  }
  closedir(DIR);


#-----------------------------------------------------------------------------------------------------
 
  &getData;

  $tableColumns =  6;
  $columnWidth  = 80;
  print qq#<table class="main">\n#;

# - - - - -

  if ( $EOMfile !~ /^\s*$/ && -e "$EOMfile" ) {
     $webpath = "/Webshare/End_of_Month/$EOMFNAME";

    print qq#<tr valign=top><th colspan=2>
    <div style="padding: 5px; background: \#FFF; border: 1px solid \#CCC; border-radius: 10px;">
      <a href="/cgi-bin/Review_My_Aging_Monthly.cgi"><font color=red>End of Month Receivables</font><span id="$disclaimer"><font color="DodgerBlue"> * </span></font></a>  
    </div></th>#;


  } else {
     print qq#<tr valign=top><th colspan=2>$nbsp</th>#;
  }

# - - - - -

  if ( $EOYfile !~ /^\s*$/ && -e "$EOYfile" ) {
     $webpath = "/Webshare/End_of_Fiscal_Year/$EOYFNAME";

    print qq#<tr valign=top><th colspan=2>
	<div style="padding: 5px; background: \#FFF; border: 1px solid \#CCC; border-radius: 10px;">
    <a href="$webpath"><font color=red>End of Fiscal Year Receivables</font><span id="$disclaimer"><font color="DodgerBlue"> * </font></span></a>
    </div></th>#;

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
  if ( $LOCENV =~ /Dev/i ) {
     $col1width = "width=250";
  } else {
     $col1width = "";
  }
  print qq#</tr>\n#;
  print qq#<tr>#;
  print qq#<th $col1width class="align_left">Third Party</th>#;
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
    $Reconcile = $TPPReconcile{$key};
    $Total     = "\$" . &commify(sprintf("$FMT", $RTotals{$key}));
    $TotalPP   = "\$" . &commify(sprintf("$FMT", $RTotalPPs{$key}));
    $F1to44    = "\$" . &commify(sprintf("$FMT", $RF1to44s{$key}));
    $F45to59   = "\$" . &commify(sprintf("$FMT", $RF45to59s{$key}));
    $F60to89   = "\$" . &commify(sprintf("$FMT", $RF60to89s{$key}));
    $Fover90   = "\$" . &commify(sprintf("$FMT", $RFover90s{$key}));
	
    if (0 == $row % 2) {
      $rowclass = "";
    } 
    else {
      $rowclass = "tan";
      $color    = '';
    }

    if ($Reconcile eq 'No') {
      $rowclass = "$rowclass font_blue";
      $color    = 'style="color:#0099ff;"';
    } 

    print qq#<tr>#;
    print qq#<td  class="$rowclass"><a href="${prog}.cgi?inTPP=${Parentkey}&inBIN=${BIN}&inBINP=${BIN}&inTPPNme=$TPP_Name" $color>$TPP_Name</a></td>#;

    print qq#<td align=right class="$rowclass">$TotalPP </td>#;
    print qq#<td align=right class="$rowclass">$F1to44</td>#;
    print qq#<td align=right class="$rowclass">$F45to59</td>#;
    print qq#<td align=right class="$rowclass">$F60to89</td>#;
    print qq#<td align=right class="$rowclass">$Fover90</td>#;
    print qq#</tr>\n#;
    $TPP_Count++;
	$row++;
  }

#-----------------------------------------------------------------------

  print qq#</td></tr>\n# if ($debug);
  &displaySwitchData;
  print qq#</table>\n#;

  if (!$disclaimer) {
  print qq#
    <p class="left font_blue">
      *Disclaimer: ReconRx cannot provide complete reconciliation
      services for <br> Third Party Payers displayed in blue. 
      These claims are not included in your aging <br> Grand Totals, or End of Month and End of Fiscal Year receivables summaries. 
    </p>
  #;
  }
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
    print qq#<tr><th class="yellow" colspan=7>No Records found for $Pharmacy_Name</th></tr>#;
  }

  print "sub displaySwitchData: Exit. qstart: $qstart, qend: $qend<br>\n" if ( $debug );
  print "<hr size=4 color=red noshade>\n" if ( $debug );

}

#______________________________________________________________________________

sub displaySingleTPP {

  my ($inTPP, $inBIN, $inBINP, $inTPPNme) = @_;
  print "sub displaySingleTPP: Entry. inTPP: $inTPP, inBIN: $inBIN, inBINP: $inBINP<br>\n" if ($debug);

  my $juser = $RUSER || $USER;
 
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

  #jQuery now loaded on all pages via header include.
  print qq#<link type="text/css" media="screen" rel="stylesheet" href="/includes/datatables/css/jquery.dataTables.css" /> \n#;
  print qq#<script type="text/javascript" charset="utf-8" src="/includes/datatables/js/jquery.dataTables.min.js"></script> \n#;
  print qq#<script type="text/javascript" charset="utf-8"> \n#;
  print qq#\$(document).ready(function() { \n#;
  print qq#                \$('\#tablef').dataTable( { \n#;
  print qq#                                "sScrollX": "100%", \n#;
  print qq#                                "bScrollCollapse": true,  \n#;
  print qq#                                "sScrollY": "350px", \n#;
  print qq#                                "bPaginate": false \n#;
  print qq#                } ); \n#;
  print qq#} ); \n#;
  print qq#</script> \n#;

  my $out;
  $out = "BIN: $inBINP";

  my ($TPPsAss) = &associated_bins($inBINP);

  print qq#<br>\n#;
  print qq#TPP: $inTPPNme<br>\n#;
  print qq#<br>\n#;
  print qq#<font size=-1><i>Codes: NP-Non Payment, PP-Partial Payment</i></font><br>\n#;

  print qq#<table id="tablef">\n#;

  print qq#<thead>\n#;
  print qq#<tr>
<th>BIN</th>
<th>Rx</th>
<th>Filled Date</th>
<th>Processed Date</th>
<th>Amount Due</th>
<th>Code</th>
\n#;
  if ( $debug ) {
    print qq#<th>PCN</th>#;
  }
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;

  my $TotalPaid;
  my $TotalPaidPP;

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

###
# 09/29/16 - BB
# Changed SQL Query
# ADDED: dbBinParent = $inBINP
###  
##&& dbBinParent   = $inBINP
  $sql = qq#
SELECT dbBinNumber, dbRxNumber,
Date_Format(dbDateOfService,'%m/%d/%Y'),
Date_Format(dbDateTransmitted,'%m/%d/%Y'),
IFNULL(dbTotalAmountPaid_Remaining,0),
IFNULL(dbTotalAmountPaid,0),
dbCode
FROM $DBNAME.incomingtb
WHERE (1=1)
&& dbNCPDPNumber = $juser
&& dbBinParentdbkey = $inTPP
&& dbCode       <> "PD"
ORDER BY $SORTFIELD
#;
  if ( $debug ) {
     $sql =~ s/dbCode\n/dbCode, dbProcessorControlNumber\n/;
  }

  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  print "<hr>1. sql:<br>$sql<hr>\n" if ($debug);

  $TotalPaidPP = 0;
  $TotalPaid   = 0;

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while (my @row = $sthrp->fetchrow_array()) {

    my ( $dbBinNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbCode );
    if ( $debug ) {
       ( $dbBinNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbCode, $dbProcessorControlNumber ) = @row;
    } else {
       ( $dbBinNumber, $dbRxNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbCode ) = @row;
    }

    next if ( $dbTotalAmountPaid == -20000);
	next if ( $dbTotalAmountPaid == 0);


#  BB - 10/07/16 - Commenting out the "WAS" display for partial payments.
#####
#    if ( $dbTotalAmountPaid == $dbTotalAmountPaid_Remaining) {
#       $addit = "";
#    } else {
#       $addit = "<br><font color=red>WAS: $dbTotalAmountPaid</font>";
#    }
#####

    print qq#<tr>#;

    print qq#<td>#, sprintf("%06d", $dbBinNumber), qq#</td>#;
    print qq#<td>$dbRxNumber</td>#;
    print qq#<td>$dbDateOfService</td>#;
    print qq#<td>$dbDateTransmitted</td>#;
    print qq#<td class="align_right">\$$dbTotalAmountPaid_Remaining</td>#;    # BB - 10/07/16 - Removing $addit value from display.
    print qq#<td class="align_center">$dbCode</td>#;
    if ( $debug ) {
       print qq#<td class="align_center">$dbProcessorControlNumber</td>#;
    }
    print qq#</tr>\n#;
    $TotalPaidPP += $dbTotalAmountPaid_Remaining;
    $TotalPaid   += $dbTotalAmountPaid;
     
  }

  $sthrp->finish;
 
# ------------------------ END. jlh. 01/06/2014. New code!


  print qq#</tbody>\n#;
  $TotalPaidPP = "\$" . &commify(sprintf("$FMT", $TotalPaidPP));
  $TotalPaid   = "\$" . &commify(sprintf("$FMT", $TotalPaid));
  print qq#<tr>#;
  print qq#</table>\n#;

  print qq#<div style="clear: both;"></div>#;
  print qq#<br>\n#;

  print qq#<div style="text-align: right; font-weight: bold; padding-right: 15px">\n#;
#
  print qq#Grand Total: $TotalPaidPP<br>\n#;

  print qq#</div>\n#;

  print qq#</FORM>\n#;

  print "sub displaySingleTPP: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________


sub associated_bins {

  my ($inBINP) = @_;
  my $TPPsAss  = "";
  my $BIN      = "";

# select Third_Party_Payer_Name from Third_Party_Payers WHERE Primary_Secondary='Pri' && BIN='$inBINP' ORDER BY Third_Party_Payer_Name;
  foreach $TPP_ID (sort { $TPP_Names{$a} cmp $TPP_Names{$b} } keys %TPP_Names) {
     next if ( $TPP_PriSecs{$TPP_ID} !~ /Pri/i );
     next if ( $TPP_BINs{$TPP_ID}    !~ /$inBINP/i );

     $TPPsAss .= "$TPP_Names{$TPP_ID}, ";
  }
  $TPPsAss =~ s/, $//g;

  return($TPPsAss);

}

#______________________________________________________________________________

sub getData {

  #Josh's Pharmacy = Buda Drug Store
  if ($inNCPDP =~ /1111111/ && $DBNAME =~ /ReconRxDB/i ) {
     $inNCPDP = 4540666;
  }
  my $show = 0;
  $show = 1 if($Pharmacy_CentralPayOrgs{$inNCPDP} eq 'Access Health');

  my $sql = "";

  $sql = qq#
SELECT totals.dbBinParentdbkey, BIN, Third_Party_Payer_Name,
(IFNULL(TotalPP1to44,0) + IFNULL(TotalPP45to59,0) + IFNULL(TotalPP60to89,0) + IFNULL(TotalPPover90,0)) TotalPP,
(IFNULL(1to44,0) + IFNULL(45to59,0) + IFNULL(60to89,0) + IFNULL(over90,0)) Total,
IFNULL(TotalPP1to44,0)  TotalPP1to44,
IFNULL(TotalPP45to59,0) TotalPP45to59,
IFNULL(TotalPP60to89,0) TotalPP60to89,
IFNULL(TotalPPover90,0) TotalPPover90,
dbProcessorControlNumber, dbGroupID, Reconcile
FROM (
SELECT dbBinParentdbkey, BIN, Third_Party_Payer_Name, sum(dbTotalAmountPaid_Remaining) TotalPP, sum(dbTotalAmountPaid) Total, dbProcessorControlNumber, dbGroupID, Reconcile
FROM $DBNAME.incomingtb 
LEFT JOIN (SELECT Third_Party_Payer_ID, Third_Party_Payer_Name, BIN, Reconcile
FROM officedb.third_party_payers) tpp 
ON dbBinParentdbkey = Third_Party_Payer_ID 
WHERE (1=1)
&& dbTotalAmountPaid_Remaining > 0 
&& dbNCPDPNumber = $inNCPDP 
&& dbCode<>"PD"
&& (tpp.Reconcile='Yes' || tpp.Reconcile='No' && $show = 1 && tpp.Third_Party_Payer_ID = 700006 )
GROUP BY dbBinParentdbkey 
ORDER BY Third_Party_Payer_Name
) totals 

LEFT JOIN (
SELECT dbBinParentdbkey, sum(dbTotalAmountPaid_Remaining) TotalPP1to44, sum(dbTotalAmountPaid) 1to44
FROM $DBNAME.incomingtb 
WHERE (1=1)
&& dbTotalAmountPaid_Remaining > 0 
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
&& dbTotalAmountPaid_Remaining > 0 
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
&& dbTotalAmountPaid_Remaining > 0 
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
&& dbTotalAmountPaid_Remaining > 0 
&& dbNCPDPNumber = $inNCPDP
&& dbCode<>"PD"
&& (DATE(dbDateTransmitted) <= (CURDATE() - INTERVAL 90 DAY))
GROUP BY dbBinParentdbkey
) set_over90 
ON set_over90.dbBinParentdbkey = totals.dbBinParentdbkey
#;

  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  print "<hr>2. sql:<br>$sqlout<hr>\n" if ($debug);

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  print "<hr>\n" if ($debug);
  while (my @row = $sthrp->fetchrow_array()) {

     print "<hr size=8 color=red noshade>\n" if ($debug);

     my ($Parentkey, $BIN, $TPP_Name, $TotalPP, $Total, $F1to44, $F45to59, $F60to89, $Fover90, $PCN, $GROUP, $Reconcile) = @row;

     print qq#BZ - ($Parentkey, $BIN, $TPP_Name, $TotalPP, $Total, $F1to44, $F45to59, $F60to89, $Fover90, $TPPID, $PCN, $GROUP)<br>\n# if ($debug);

     next if ( $Parentkey == -1 );	# jlh. 12/20/2013. For Tori!!!!

     print "Parentkey: $Parentkey, dbBinParents(): $dbBinParents{$Parentkey}, 2: $dbBinParents{$BIN}<br>\n" if ($debug);
     my $keyBinNumber = $dbBinParents{$Parentkey} || $BIN;
     my $TPPID = "";    

     $PCN   =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white space
     $GROUP =~ s/^\s*(.*?)\s*$/$1/;
     $TPP_Name     =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces
     
     $disclaimer = ''    if ($Reconcile eq 'No');
     $key = "$TPP_Name";
     $RParentkeys{$key}  = $Parentkey;
     $RBINs{$key}        = $BIN;
     $RTPP_Names{$key}   = $TPP_Name;
     $TPPReconcile{$key} = $Reconcile;
     $RTotals{$key}     += $Total;
     $RTotalPPs{$key}   += $TotalPP;
     $RF1to44s{$key}    += $F1to44;
     $RF45to59s{$key}   += $F45to59;
     $RF60to89s{$key}   += $F60to89;
     $RFover90s{$key}   += $Fover90;
     if ($Reconcile eq 'Yes') {
       $Grand_RTotals     += $Total;
       $Grand_RTotalPPs   += $TotalPP;
       $Grand_RF1to44s    += $F1to44;
       $Grand_RF45to59s   += $F45to59;
       $Grand_RF60to89s   += $F60to89;
       $Grand_RFover90s   += $Fover90;
     }

  }
  $sthrp->finish;
 
}

