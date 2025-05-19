require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; 
my $start = time();
($prog, $dir, $ext) = fileparse($0, '\..*');
$PROG = "$prog" . "$ext";

$ret = &ReadParse(*in);

&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$inTPP      = $in{'inTPP'};
$inBIN      = $in{'inBIN'};
$inBINP     = $in{'inBINP'};
$inTPPNme   = $in{'inTPPNme'};
$SORT       = $in{'SORT'};
my $ag      = 0;

($inTPP) = &StripJunk($inTPP);
($inBIN) = &StripJunk($inBIN);
($inBINP)= &StripJunk($inBINP);

#______________________________________________________________________________

&readsetCookies;
#______________________________________________________________________________
# Create the inputfile format name
my  $Agg;
my  $Agg2;
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$CHECKYEAR = $year + 1;

#______________________________________________________________________________

&readPharmacies;

if ( $USER ) {
  $inNCPDP = $Pharmacy_NCPDPs{$PH_ID};
  &MyReconRxHeader;
  if ( $PH_ID  eq 'Aggregated') {
    $ag = 1;
    $Agg  = "\\Aggregated";
    $Agg2 = "/Aggregated";
    $inNCPDP = $USER;
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

if ( $PH_ID  eq 'Aggregated') {
  $PH_ID = $Agg_String;
}

#______________________________________________________________________________

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

if ($PH_ID == 11 || $PH_ID == 23 || $PH_ID eq "11,23") {
	$DBNAME = "webinar";
}

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
   print qq#<a class="text_navy" href="javascript:history.go(-1)"> Go Back</a><br>\n#;
   &displaySingleTPP($inTPP, $inBIN, $inBINP, $inTPPNme);
} else {
   $ntitle = "Aging Report";
   print qq#<h1 class="page_title">$ntitle</h1>\n#;
   &displayWebPage;
}

$dbx->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {
  print qq#<!-- displayWebPage -->\n#;

  ($PROG = $prog) =~ s/_/ /g;

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
     ($qstart, $qend) = &calcRanges($start, $end);
     $JSTART{$DR} = $qstart;
     $JEND{$DR}   = $qend;
  }

###################################################################################
# Look for End_of_Fiscal_Year file
 
  if ( $ENV =~ /Dev/i ) {
     $outdir    = qq#D:\\WWW\\www.recon-rx.com\\WebShare\\End_of_Fiscal_Year$Agg#;
  } else {
     $outdir    = qq#D:\\WWW\\members.recon-rx.com\\WebShare\\End_of_Fiscal_Year$Agg#;
  }

  my $EOYfile   = "";
  my $EOYFNAME  = "";
  my $savemtime =  0;
# CHECKYEAR set at top

  for ( $CKYEAR=$CHECKYEAR; $CKYEAR >= $CHECKYEAR-3; $CKYEAR-- ) {
     opendir(DIR, "$outdir") or die $outdir ;
     while (my $fname = readdir(DIR)) {
        $tmp = $PH_ID; 
        $tmp = 'Aggregated' if ($ag);

        next if ( $fname =~ m/^\./ );
        next if ( $fname !~ /${inNCPDP}_${tmp}_${CKYEAR}/ );
        if ( $fname =~ /${inNCPDP}_${tmp}_${CKYEAR}/ ) {
           $found++;
           $EOYFNAME  = $fname;
           $EOYfile   = "$outdir\\$fname";
           $mtime     = (stat "$EOYfile")[9];
           $savemtime = $mtime;
        }
        last if ( $found);
     }
     closedir(DIR);
     last if ( $found);
  }

###################################################################################
# Look for End_of_Month file
  if ( $ENV =~ /Dev/i ) {
     $outdir    = qq#D:\\WWW\\www.recon-rx.com\\WebShare\\End_of_Month$Agg#;
  } else {
     $outdir    = qq#D:\\WWW\\members.recon-rx.com\\WebShare\\End_of_Month$Agg#;
  }

  my $EOMfile  = "";
  my $EOMFNAME    = "";
  my $EOMdisp = "";

  opendir(DIR, "$outdir") or die $!;
  while (my $fname = readdir(DIR)) {
     next if ( $fname =~ m/^\./ );
     next if ( $fname !~ /${inNCPDP}_/ );

     $EOMfile  = "$outdir\\$fname";
     $mtime = (stat "$EOMfile")[9];
     if ( (time() - $mtime) <= $sixmonths ) {
        $EOMFNAME = $fname;
        $EOMdisp = 1;
     } else {
        $EOMfile = "";
        $EOMFNAME   = "";
     }
  }
  closedir(DIR);

###################################################################################

#-----------------------------------------------------------------------------------------------------
 
  &getData;

  $tableColumns =  6;
  $columnWidth  = 100;
  print qq#<table class="main">\n#;

# - - - - -
  ##my $menuoption = &getMenuOption;
##
##  if($ag) {
##    if ( $EOMdisp ) {
##      $webpath = "/Webshare/End_of_Month$Agg2/$EOMFNAME";
##      print qq#<tr valign=top><th>
##	<div style="padding: 5px; background: \#5FC8ED; border: none;">
##        <a href="/cgi-bin/Review_My_Accounts_Receivable_Monthly.cgi"><font color=white>End of Month Receivables</font></a>
##       </div></th>#;
##    } 
##    else {
##      print qq#<tr valign=top><th colspan=2>$nbsp</th>#;
##    }
##
# - - - - -

##    if ( $EOYfile !~ /^\s*$/ && -e "$EOYfile" ) {
##      $webpath = "/Webshare/End_of_Fiscal_Year$Agg2/$EOYFNAME";
##      print qq#<tr valign=top><th>
##       <div style="padding: 5px; background: \#5FC8ED; border: none;">
##       <a href="Review_My_Accounts_Receivable_Yearly.cgi"><font color=white>End of Fiscal Year Receivables</font></a>
##       </div></th>#;
##    } 
##    else {
##      print qq#<tr valign=top><th colspan=2>$nbsp</th>#;
##    }
##  }

#  foreach $DR (sort { $a <=> $b } keys %DateRanges ) {
#     my $start = substr($JSTART{$DR},4,2) . "/" . substr($JSTART{$DR},6,2) . "/" . substr($JSTART{$DR},0,4);
#     my $end   = substr($JEND{$DR},4,2) . "/" . substr($JEND{$DR},6,2) . "/" . substr($JEND{$DR},0,4);
#     if ( $DR == 4 ) {
#        print qq#<th class="align_center"><font size=-1>$start<br>and<br>Older</font></th>#;
#     } else {
#        print qq#<th class="align_center"><font size=-1>$start thru $end</font></th>#;
#     }
#  }

#  if ( $LOCENV =~ /Dev/i ) {
#     $col1width = "width=250";
#  } else {
     $col1width = "";
#  }

  print qq#</tr>\n#;
  print qq#<tr>#;
  print qq#<th $col1width class="align_left lj_blue_bb">Third Party</th>#;
  print qq#<th class="align_right lj_blue_bb">Total</th>#;

  foreach $DR (sort { $a <=> $b } keys %DateRanges) {
     $DRNext = $DR + 1;
     $start = $DateRanges{$DR};
     $end   = $DateRanges{$DRNext} - 1;
     if ( !$start ) {
        print qq#<th class="align_right lj_blue_bb" width=$columnWidth>1-$end</th>#;
     } else {
        if ( $DR == 4 ) {
           print qq#<th class="align_right lj_blue_bb" width=$columnWidth>$DateRanges{$DR}+</th>#;
        } else {
           print qq#<th class="align_right lj_blue_bb" width=$columnWidth>$start-$end</th>#;
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
      $rowclass = "lj_blue_table";
    } else {
      $rowclass = "";
    }

    print qq#<tr>#;
    print qq#<td class="$rowclass"><a class="$rowclass" href="${prog}.cgi?inTPP=${Parentkey}&inBIN=${BIN}&inBINP=${BIN}&inTPPNme=$TPP_Name">$TPP_Name</a></td>#;

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

  &displaySwitchData;
  print qq#</table>\n#;
=cut
  if($menuoption ne 'Yes') {
    if (!$ag) {
    print qq#
    <p class="center">
      <span style="font-weight: bold; font-size: 120%;"><a class="text_navy" href="Review_My_Aging_Detailed.cgi">Click here to Create Detailed Aging File</a></span>
    </p>
    #;
    }
  }
=cut

  print "sub displayWebPage: Exit.<br>\n" if ($debug);
}

#______________________________________________________________________________

sub displaySwitchData {
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
  print qq#<th class="lj_blue_bt">Grand Totals</th>#;
  print qq#<th class="money lj_blue_bt" bgcolor=yellow>$Grand_RTotals</th># if ($LOCENV =~ /Dev/i);
  print qq#<th class="money lj_blue_bt">$Grand_RTotalPPs</th>#;
  print qq#<th class="money lj_blue_bt">$Grand_RF1to44s</th>#;
  print qq#<th class="money lj_blue_bt">$Grand_RF45to59s</th>#;
  print qq#<th class="money lj_blue_bt">$Grand_RF60to89s</th>#;
  print qq#<th class="money lj_blue_bt">$Grand_RFover90s</th>#;
  print qq#</tr>\n#;

  if ( $TPP_Count <= 0 ) {
    print qq#<tr><th class="yellow" colspan=7>No Records found for $Pharmacy_Name</th></tr>#;
  }
}

#______________________________________________________________________________

sub displaySingleTPP {
  my ($inTPP, $inBIN, $inBINP, $inTPPNme) = @_;

  $URLH = "${prog}.cgi";
  print qq#<FORM ACTION="$URLH" METHOD="POST">\n#;
  print qq#<INPUT TYPE="hidden" NAME="db"      VALUE="$dbin">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inTPP"   VALUE="$inTPP">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inBIN"   VALUE="$inBIN">\n#;
  print qq#<INPUT TYPE="hidden" NAME="inBINP"  VALUE="$inBINP">\n#;

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
  print qq#<span style="font-weight: bold">TPP: $inTPPNme</span><br>\n#;
  print qq#<br>\n#;

  print qq#<table id="tablef">\n#;

  print qq#<thead>\n#;
  print qq#<tr>\n#;

  if ($ag == 1) {
    print qq#<th width=50>NCPDP</th>#;
  }

  print qq#
             <th width=100>BIN</th>
             <th width=100>PCN</th>
             <th width=50>Rx</th>
             <th width=50>Fill Number</th>
             <th width=50>Filled Date</th>
             <th width=50>Processed Date</th>
             <th width=50>Prescriber ID</th>
             <th width=50>Amount Due</th>
        \n#;
  print qq#</tr>\n#;
  print qq#</thead>\n#;

  print qq#<tbody>\n#;

  my $TotalPaid;
  my $TotalPaidPP;
      $SORTFIELD = "dbNCPDPNumber";

  my $sql = "";

  $sql = "SELECT dbNCPDPNumber, dbBinNumber, dbRxNumber, dbFillNumber, Date_Format(dbDateOfService,'%m/%d/%Y'), Date_Format(SUBSTR(dbDateTransmitted,1,8),'%m/%d/%Y'),
                 IFNULL(dbTotalAmountPaid_Remaining,0), IFNULL(dbTotalAmountPaid,0), dbProcessorControlNumber, dbPrescriberID
            FROM $DBNAME.incomingtb
           WHERE pharmacy_id IN ($PH_ID)
              && dbBinParentdbkey = $inTPP
              && dbTCode IN ('','PP')
        ORDER BY $SORTFIELD";

  ($sqlout = $sql) =~ s/\n/<br>\n/g;
  print "<hr>1. sql:<br>$sql<hr>\n" if ($debug);

  $TotalPaidPP = 0;
  $TotalPaid   = 0;

  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while ( my ( $dbNCPDPNumber, $dbBinNumber, $dbRxNumber, $dbFillNumber, $dbDateOfService, $dbDateTransmitted, $dbTotalAmountPaid_Remaining, $dbTotalAmountPaid, $dbProcessorControlNumber,$dbPrescriberID ) = $sthrp->fetchrow_array()) {
    next if ( $dbTotalAmountPaid == -20000);
    next if ( $dbTotalAmountPaid == 0);

    print qq#<tr>#;

    if ($ag == 1) {
      print qq#<td>#, sprintf("%07d", $dbNCPDPNumber), qq#</td>#;
    }
    print qq#<td>#, sprintf("%06d", $dbBinNumber), qq#</td>#;
    print qq#<td>$dbProcessorControlNumber</td>#;
    print qq#<td>$dbRxNumber</td>#;
    print qq#<td>#, sprintf("%02d", $dbFillNumber), qq#</td>#;
    print qq#<td>$dbDateOfService</td>#;
    print qq#<td>$dbDateTransmitted</td>#;
    print qq#<td>$dbPrescriberID</td>#;
    print qq#<td class="align_right">$dbTotalAmountPaid_Remaining</td>#;
    print qq#</tr>\n#;
    $TotalPaidPP += $dbTotalAmountPaid_Remaining;
    $TotalPaid   += $dbTotalAmountPaid;
     
  }

  $sthrp->finish;
 
  print qq#</tbody>\n#;
  $TotalPaidPP = "\$" . &commify(sprintf("$FMT", $TotalPaidPP));
  $TotalPaid   = "\$" . &commify(sprintf("$FMT", $TotalPaid));
  print qq#<tr>#;
  print qq#</table>\n#;

  print qq#<div style="clear: both;"></div>#;
  print qq#<br>\n#;

  print qq#<div style="text-align: right; font-weight: bold; padding-right: 15px">\n#;

  print qq#Grand Total: $TotalPaidPP<br>\n#;

  print qq#</div>\n#;

  print qq#</FORM>\n#;
}

#______________________________________________________________________________

sub associated_bins {
  my ($inBINP) = @_;
  my $TPPsAss  = "";
  my $BIN      = "";

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
  $display_esi = '';

   #if ($PH_ID == 11 && $DBNAME =~ /ReconRxDB/i ) {
   #   $PH_ID = 248;
   #}
  
  #print "PH_ID: $PH_ID  USER: $USER\n";
##Removed per Jessie 20220202
##  if ($Pharmacy_DisplayESI{$PH_ID} =~ /^Y$/) {
##     $display_esi = 1;
##     ##$TPP_Reconciles{'700006'} = 'Yes';
##  }
    
  

  $reconrx_aging_sql = &get_reconrx_aging_sql($PH_ID,$display_esi);

  my $sql =" SELECT TPP_ID, dbBinNumber, Third_Party_Payer_Name, sum(dbTotalAmountPaid_Remaining) as 'Total', sum(`1-44 Days`) as a, sum(`45-59 Days`) as b, sum(`60-89 Days`) as c ,sum(`90+ Days`) as d 
             FROM ($reconrx_aging_sql
                  )a
            GROUP BY TPP_ID";
  #print "sql: $sql\n";
  $sthrp = $dbx->prepare($sql);
  $sthrp->execute();
  my $numofrows = $sthrp->rows;

  while ( my ($Parentkey, $BIN, $TPP_Name, $TotalPP, $F1to44, $F45to59, $F60to89, $Fover90, $PCN, $GROUP) = $sthrp->fetchrow_array()) {
    if ($PH_ID =~ /^23$|^4$|^11$/ ) {
      $TotalPP -= $F60to89;
      $TotalPP -= $Fover90;
      $F60to89  = 0;
      $Fover90 = 0;
    }
     next if ( $Parentkey == -1 );

     my $keyBinNumber = $dbBinParents{$Parentkey} || $BIN;
     my $TPPID = "";    

     $PCN   =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white space
     $GROUP =~ s/^\s*(.*?)\s*$/$1/;

     ##my ($jbin, $new_TPP_Name) = split("\-", $MyPrimary, 2);
     $TPP_Name     =~ s/^\s*(.*?)\s*$/$1/;    # trim leading and trailing white spaces

     $key = "$TPP_Name";

     $RParentkeys{$key}  = $Parentkey;
     $RBINs{$key}        = $BIN;
     $RTPP_Names{$key}   = $TPP_Name;
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

#________________________________________
#;______________________________________
