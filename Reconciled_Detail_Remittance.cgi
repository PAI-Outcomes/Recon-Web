
require "D:/RedeemRx/MyData/RBSDesktop_routines.pl";
require "D:/RedeemRx/cgi-bin/cgi-lib.pl";

use File::Basename;
use CGI::Carp qw(fatalsToBrowser warningsToBrowser);
use Time::Local;
use Env qw(PATH REMOTE_ADDR PERL5LIB PERLLIB);

$| = 1; # don't buffer output

($prog, $dir, $ext) = fileparse($0, '\..*');
$nbsp = "&nbsp;";

$ret = &ReadParse(*in);

# A bit of error checking never hurt anyone
&CgiDie("Error in reading and parsing of CGI input") if !defined $ret;

$RADIO      = $in{'RADIO'};

#______________________________________________________________________________

&readsetCookies;
&readPharmacies;

#______________________________________________________________________________

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

#______________________________________________________________________________
# Create the inputfile format name
my ($min, $hour, $day, $month, $year) = (localtime)[1,2,3,4,5];
$year  += 1900;	# reported as "years since 1900".
$month += 1;	# reported ast 0-11, 0==January
$syear  = sprintf("%4d", $year);
$fileyear = $syear - 1;
$smonth = sprintf("%02d", $month);
$sday   = sprintf("%02d", $day);
$tdate  = sprintf("%04d/%02d/%02d", $year, $month, $day);
$ttime  = sprintf("%02d:%02d", $hour, $min);
$testdate= sprintf("%04d%02d%02d", $year, $month, $day);
#______________________________________________________________________________

$skipdate   = "1970-01-01";
($skipdatewo = $skipdate) =~ s/-//g;

if ( $MaxEntries ) {
     # Do nothing, already entered on command line
} else {
   $MaxEntries = 26;	# WEEKS - jlh. 03/14/2017 Asked to changed from 12 to 26
   $MaxEntries = 80 if ($PH_ID =~ /399|762|225/);
   $MaxEntries = 80 if($AreteUser);
}


#______________________________________________________________________________

$dbin     = "R8DBNAME";
$DBNAMER8 = $DBNAMES{"$dbin"};
$TABLER8  = $DBTABN{"$dbin"};

$dbin     = "P8DBNAME";
$DBNAMEP8 = $DBNAMES{"$dbin"};
$TABLEP8  = $DBTABN{"$dbin"};

if ($PH_ID == 11 || $PH_ID == 23) {
	$DBNAME   = "webinar";
} else {
	$DBNAME   = $DBNAMER8;
}

%records = ();
%rec2    = ();

my  $Agg;
my  $Agg2;
my $ag = 0;

$dbz = DBI->connect("DBI:mysql:$DBNAME:$DBHOST",$dbuser,$dbpwd,
       { PrintError => 1, RaiseError => 1, InactiveDestroy => 0 } ) || die "$DBI::errstr";
DBI->trace(1) if ($dbitrace);

$ntitle = "Payment Dates";
print qq#<h1 class="page_title">$ntitle</h1>\n#;
&displayWebPage;

$dbz->disconnect;

#______________________________________________________________________________

&MyReconRxTrailer;

exit(0);

#______________________________________________________________________________

sub displayWebPage {

   if ($PH_ID  =~ /Aggregated/i ) {
     $ag = 1;
     $PH_ID = $Agg_String;
     $Agg  = "\\Aggregated";
     $Agg2 = "/Aggregated";
   }
   if ($PH_ID == "11,23") {
	   $DBNAME = "webinar";
   }
   print qq#<!-- displayWebPage -->\n#;

   $FMT = "%0.02f";
   my @abbr = qw( Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec );

   my $TOTAL      = 0;
   my $GRANDTOTAL = 0;
   my $hoursinday = 60 * 60 * 24;
   my %Unique_Dates = ();
   my $CHECKEDCRD = "";
   my $CHECKEDCD  = "";
   my $FIELDTITLE = "";
   my $Q          = "";
   my $EOYFName = "ReconRx_End_of_Fiscal_Year_Reconciled_Claims_Summary_${inNCPDP}_${PH_ID}_$fileyear.xlsx";
   my $EOYfile  = '';

   if ($ag) {
      $EOYFName = "ReconRx_End_of_Fiscal_Year_Reconciled_Claims_Summary_${USER}_Aggregated_$fileyear.xlsx";
   }

   $testing = '_TEST' if ( $ENV =~ /Dev/i );
   my $outdir    = qq#D:\\WWW\\members.recon-rx.com\\WebShare\\End_of_Fiscal_Year_Reconciled_Claims$Agg#;
  
   $EOYfile   = "$outdir\\$EOYFName";

   if ( $RADIO =~ /Received/i || $RADIO =~ /^\s*$/ ) {
     $CHECKEDCD  = "";
     $CHECKEDCRD = "CHECKED";
     $FIELDTITLE = "Check Received Date";
     $Q          = "CRD";
   } else {
     $CHECKEDCD  = "CHECKED";
     $CHECKEDCRD = "";
     $FIELDTITLE = "Check Date";
     $Q          = "CD";
   }

  print qq#ADD db query condition like "only display records for this logged in pharmacy, unless I'm an admin"<br><br>\n# if ($debug);

     my $sql = "SELECT R_TPP, R_TS3_NCPDP, R_BPR04_Payment_Method_Code, R_BPR02_Check_Amount, R_BPR03_CreditDebit_Flag_Code,
                       R_BPR16_Date, R_TRN02_Check_Number, '', IFNULL(R_CheckReceived_Date,'$skipdate'), R_PENDRECV, Pharmacy_ID
                  FROM $DBNAME.checks
                 WHERE Pharmacy_ID IN ($PH_ID)
                    && R_CheckReceived_Date > '1901-01-01' 
                    && R_PENDRECV = 'R'";

     if ( $Q =~ /CRD/i ) {
        $sql .= " ORDER BY R_CheckReceived_Date DESC ";
     } else {
        $sql .= " ORDER BY R_BPR16_Date DESC ";
     }
     #print "sql: $sql\n";
     ($sqlout = $sql) =~ s/\n/<br>\n/g;
     print "sql:<br>$sqlout<P>\n" if ($verbose);

     $stj = $dbz->prepare($sql);
     $numofrows = $stj->execute;
     print "Rows found: numofrows: $numofrows in Tables: $TABLER8/$TABLEP8<br><br>\n" if ($debug);
  
     if ( $numofrows > 0 ) {
       while (my @row = $stj->fetchrow_array()) {
         ($R_TPP, $R_TS3_NCPDP, $R_BPR04_Payment_Method_Code, $R_BPR02_Check_Amount, $R_BPR03_CreditDebit_Flag_Code, $R_BPR16_Date, $R_TRN02_Check_Number, $R_Reconciled_Date, $R_CheckReceived_Date) = @row;
        if ( $Q =~ /CRD/i ) {
           $key = "$R_CheckReceived_Date";
         } else {
           $key = "$R_BPR16_Date";
         }
         $key =~ s/\-//g;


         $records{$key}++;
         $checkamounts{$key} = $R_BPR02_Check_Amount;
         $sortdates{$key}    = $key;
         $Unique_Dates{"$key"} = $key;
         $jdate = $key;

         $sorttotals{$key} += $R_BPR02_Check_Amount;
       }
     }
     $stj->finish;

     print qq#<table class="main">\n#;
     print qq#<tr valign=top><td class="multi_table">\n#;
     print qq#<table>\n#;

     print qq#<FORM ACTION="$prog.cgi" METHOD="POST">\n#;

     print qq# <INPUT TYPE="hidden" NAME="MaxEntries" VALUE=$MaxEntries\n#;
     print qq# <INPUT TYPE="hidden" NAME="debug"      VALUE=$debug\n#;
     print qq# <INPUT TYPE="hidden" NAME="verbose"    VALUE=$verbose\n#;

     print qq#<tr valign=top>\n#;
     print qq#<th> Display by:<br>#;
     print qq# <INPUT TYPE="radio" NAME="RADIO" VALUE="Check Received Date" $CHECKEDCRD onclick="this.form.submit();">Check Received Date<br>\n#;
     print qq# <INPUT TYPE="radio" NAME="RADIO" VALUE="Check Date"          $CHECKEDCD  onclick="this.form.submit();">Check Date</th>\n#;

     print qq#</tr>\n#;

     print qq#</FORM>\n#;

     print qq#<tr valign=top>\n#;
        print qq#<th nowrap>$FIELDTITLE<br><font size=-2>(Click on Date for Detail)</font></th>\n#;
        print qq#<th class="align_right">Total Amount</th>\n#;
  
     %seen = ();
  
     my $LimitCount = 0;

     my $now = time();
     my $weeks_ago = $now - ($MaxEntries * 7 * 24 * 60 * 60);	# Number of Weeks
     my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($weeks_ago);
     $mon++;
     $year = $year + 1900;
     $gtdate = sprintf("%04d%02d%02d", $year, $mon, $mday);

     print "<hr>\n";

     foreach $DATE (sort { $b <=> $a } keys %Unique_Dates) {
       if ( $FIELDTITLE =~ /Check Received Date/ && $DATE == $testdate) {
          print "DATE: $DATE - testdate: $testdate : SKIPPING!!!!<br>\n" if ($debug);
          next;
       }

       next if ( $gtdate > $DATE );

       foreach $key (sort keys %sorttotals) {
          $jdate = $sortdates{$key};
          next if ( $DATE != $jdate );

          next if ( $DATE eq $skipdatewo );

          $count = $records{$key};
  
          $year = substr($jdate, 0, 4);
          $mon  = substr($jdate, 4, 2);
          $mday = substr($jdate, 6, 2);
          $sec = 0; $min = 0; $hour = 0;
          $mon = $mon - 1;	# For indexing into abbr array
          $TIME = timelocal($sec,$min,$hour,$mday,$mon,$year);
          $date = qq#$abbr[$mon] $mday, $year#; 
  
          if ( !$seen{"$jdate"}) {
             $daily = $sorttotals{$key};
             $seen{"$jdate"}++;
             my $dailyout = "\$" . &commify(sprintf("$FMT", $daily));
             print qq#<tr><td><a href="TPP_Checklist.cgi?Q=$Q&TS=$TIME">$date</a></td> <td class="align_right">$dailyout</td></tr>\n#;
    
             $GRANDTOTAL += $daily;

             # Now add up TPP data
             my $value = sprintf("$FMT", $daily);
             my @pcs = split("##", $key);
             my $key2 = $pcs[0];
             # print "key2: $key2, value: $value<br>\n";
             if ( $R_CheckReceived_Date) {
                $TPP_Totals{$key2} += $value;
                $GrandTotal_TPP_Totals += $value;
             }
          }
       }
     }
  
     my $TOTALout = "\$" . &commify(sprintf("$FMT", $GRANDTOTAL));
     print qq#<tr><th>TOTAL</th> <th class="align_right">$TOTALout</th></tr>\n#;
     print qq#</table>\n#;
     print qq#</td><td class="multi_table">\n#;
     print "<hr>\n";

     my $menuoption = &getMenuOption;

     if($ag) { 
       print qq#<table class='main'>\n#;
       print qq#<tr><th>
       <div style="padding: 5px; background: \#5FC8ED;">
         <a href="/cgi-bin/Review_My_Reconciled_Claims_Monthly.cgi"><font color=\#FFF>End of Month Reconciled Claims Summary</font></a>
       </div></th>#;
       if (-e "$EOYfile" ) {
         $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Fiscal_Year_Reconciled_Claims$testing/$EOYFName";
         if ($ag) {
           $webpath = "https://${ENV}.Recon-Rx.com/Webshare/End_of_Fiscal_Year_Reconciled_Claims${Agg2}/$EOYFName";
         }
         print qq#<tr><th>
         <div style="padding: 5px; background: \#5FC8ED;">
           <a href="Review_My_Reconciled_Claims_Yearly.cgi"><font color=\#FFF>End of Year Reconciled Claims Summary</font></a>
         </div></th>#;
       } 
       else {
         print qq#<tr><th>$nbsp</th>#;
       }

       if ( $Pharmacy_Wants835Files{$PH_ID} =~ /Yes/ ) {
         print qq#<tr><th>
         <div style="padding: 5px; background: \#5FC8ED;">
           <a href="/cgi-bin/Bulk_835_Download.cgi"><font color=\#FFF>Bulk 835 File Download</font></a>
         </div></th>#;
       } 
       else {
         print qq#<tr><th>$nbsp</th>#;
       }
       print qq#</table>\n#;
       print qq#</td></tr>\n#;
     }

     print qq#</td></tr>\n#;
     print qq#</table>\n#;
}

