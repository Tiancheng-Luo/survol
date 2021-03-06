# This optional module aggregates function calls into bigger sequences.
# It is not necessary for Docker files.
# All functions calls and all objects are processed identically.
# It just detects repetitions of identical parameters.

import sys
import datetime

# TODO: It should not depend on this package.
if __name__ == '__main__':
    import linux_api_definitions
else:
    from . import linux_api_definitions

def _SignatureForRepetitions(batchRange):
    return "+".join( [ aBtch.get_signature_with_args() for aBtch in batchRange ] )

# This groups several contiguous BatchLet which form a logical operation.
# For example (If the argument is factorised).:
#   Read(x)
#   Write(x)
#
# ... or ...
#   fseek("dummy.txt")
#   fwrite("dummy.txt")
#
# There can be several way to "reuse" a sequence, depending on other similar
# sequences.
#
class BatchLetSequence(linux_api_definitions.BatchLetBase, object):
    def __init__(self,arrBatch,style):
        batchCore = linux_api_definitions.BatchLetCore()

        # TODO: Instead of a string, this could be a tuple because it is hashable.
        concatSigns = "+".join( [ btch.get_signature_without_args() for btch in arrBatch ] )
        batchCore._function_name = "(" + concatSigns + ")"

        batchCore.m_status = linux_api_definitions.BatchStatus.sequence

        # sys.stdout.write("BatchLetSequence concatSigns=%s\n"%concatSigns)

        # This is returned by the method get_significant_args()

        # Cannot use a set because lists are not hashable, and objects always different.
        # Because there are very few arguments, it is allright to iterate on each list.
        argsArray = []
        for btch in arrBatch:
            for oneArg in btch.get_significant_args():
                if not oneArg in argsArray:
                    argsArray.append( oneArg )
        batchCore.m_parsedArgs = argsArray

        # All batchlets should have the same pid.
        batchCore.m_pid = arrBatch[0].m_core.m_pid

        batchCore._time_start = arrBatch[0].m_core._time_start
        batchCore._time_end = arrBatch[-1].m_core._time_end
        batchCore.m_execTim = datetime.datetime.strptime(batchCore._time_end, '%H:%M:%S.%f') - datetime.datetime.strptime(batchCore._time_start, '%H:%M:%S.%f')

        super( BatchLetSequence,self).__init__(batchCore,style)


# This is an execution flow, associated to a process. And a thread ?
class BatchFlow:
    def __init__(self):

        self.m_listBatchLets = []
        self.m_coroutine = self.__adding_coroutine()
        next(self.m_coroutine)

    # It processes system calls on-the-fly without intermediate storage.
    def append_batch_to_flow(self, btchLet):
        self.m_coroutine.send(btchLet)

    def __adding_coroutine(self):
        lstBatch = None
        while True:
            btchLet = yield

            if lstBatch and lstBatch.is_same_call(btchLet):
                # This is a compression: Similar and consecutive calls are stored once only.
                lstBatch.m_occurrences += 1
            else:
                self.m_listBatchLets.append(btchLet)
            # Intentionally points to the object actually stored in the container,
            # instead of the possibly transient object returned by yield.
            lstBatch = self.m_listBatchLets[-1]

    # This removes matched batches (Formerly unfinished calls which were matched to the resumed part)
    # when the merged batches (The resumed calls) comes immediately after.
    def __filter_matched_batches(self):
        lenBatch = len(self.m_listBatchLets)

        numSubst = 0
        idxBatch = 1
        while idxBatch < lenBatch:
            # sys.stdout.write("FilterMatchedBatches idxBatch=%d\n"%( idxBatch ) )
            batchSeq = self.m_listBatchLets[idxBatch]
            batchSeqPrev = self.m_listBatchLets[idxBatch - 1]

            # Sanity check.
            if batchSeqPrev.m_core.m_status == linux_api_definitions.BatchStatus.matched \
                    and batchSeq.m_core.m_status == linux_api_definitions.BatchStatus.merged:
                if batchSeqPrev.m_core._function_name != batchSeq.m_core._function_name:
                    raise Exception(
                        "INCONSISTENCY1 %s %s\n" % (batchSeq.m_core._function_name, batchSeqPrev.m_core._function_name))

            if batchSeqPrev.m_core.m_status == linux_api_definitions.BatchStatus.matched \
                    and batchSeq.m_core.m_status == linux_api_definitions.BatchStatus.merged:
                if batchSeqPrev.m_core.m_resumedBatch.m_unfinishedBatch != batchSeqPrev.m_core:
                    raise Exception("INCONSISTENCY2 %s\n" % batchSeqPrev.m_core._function_name)

            if batchSeqPrev.m_core.m_status == linux_api_definitions.BatchStatus.matched \
                    and batchSeq.m_core.m_status == linux_api_definitions.BatchStatus.merged:
                if batchSeq.m_core.m_unfinishedBatch.m_resumedBatch != batchSeq.m_core:
                    raise Exception("INCONSISTENCY3 %s\n" % batchSeq.m_core._function_name)

            if batchSeqPrev.m_core.m_status == linux_api_definitions.BatchStatus.matched \
                    and batchSeq.m_core.m_status == linux_api_definitions.BatchStatus.merged \
                    and batchSeqPrev.m_core.m_resumedBatch == batchSeq.m_core \
                    and batchSeq.m_core.m_unfinishedBatch == batchSeqPrev.m_core:
                del self.m_listBatchLets[idxBatch - 1]
                batchSeq.m_core.m_unfinishedBatch = None
                lenBatch -= 1
                numSubst += 1

            idxBatch += 1

        return numSubst

    # This counts the frequency of consecutive pairs of calls.
    # Used to replace these common pairs by an aggregate call.
    # See https://en.wikipedia.org/wiki/N-gram about bigrams.
    # About statistics: https://books.google.com/ngrams/info
    def __statistics_bigrams(self):

        lenBatch = len(self.m_listBatchLets)

        mapOccurences = {}

        idxBatch = 0
        maxIdx = lenBatch - 1
        while idxBatch < maxIdx:
            batchRange = self.m_listBatchLets[idxBatch: idxBatch + 2]

            keyRange = _SignatureForRepetitions(batchRange)

            try:
                mapOccurences[keyRange] += 1
            except KeyError:
                mapOccurences[keyRange] = 1
            idxBatch += 1

        return mapOccurences

    # This examines pairs of consecutive calls with their arguments, and if a pair
    # occurs often enough, it is replaced by a single BatchLetSequence which represents it.
    def __clusterize_bigrams(self):
        lenBatch = len(self.m_listBatchLets)

        mapOccurences = self.__statistics_bigrams()

        numSubst = 0
        idxBatch = 0
        maxIdx = lenBatch - 1
        batchSeqPrev = None
        while idxBatch < maxIdx:

            batchRange = self.m_listBatchLets[idxBatch: idxBatch + 2]
            keyRange = _SignatureForRepetitions(batchRange)
            numOccur = mapOccurences.get(keyRange, 0)

            # Five occurences for example, as representative of a repetition.
            if numOccur > 5:
                batchSequence = BatchLetSequence(batchRange, "Rept")

                # Maybe it is the same as the previous element, if this is a periodic pattern.
                if batchSeqPrev and batchSequence.is_same_call(batchSeqPrev):
                    # Simply reuse the previous batch.
                    batchSeqPrev.m_occurrences += 1
                    del self.m_listBatchLets[idxBatch: idxBatch + 2]
                    maxIdx -= 2
                else:
                    self.m_listBatchLets[idxBatch: idxBatch + 2] = [batchSequence]
                    maxIdx -= 1
                    batchSeqPrev = batchSequence
                    idxBatch += 1

                numSubst += 1
            else:
                batchSeqPrev = None
                idxBatch += 1

        return numSubst

    # Successive calls which have the same arguments are clusterized into logical entities.
    def __clusterize_batches_by_arguments(self):
        lenBatch = len(self.m_listBatchLets)

        numSubst = 0
        idxLast = 0
        idxBatch = 1
        while idxBatch <= lenBatch:
            if idxBatch < lenBatch:
                lastBatch = self.m_listBatchLets[idxLast]
                lastArgs = lastBatch.get_significant_args()
                if not lastArgs:
                    idxLast += 1
                    idxBatch += 1
                    continue

                currentBatch = self.m_listBatchLets[idxBatch]

                if currentBatch.get_significant_args() == lastArgs:
                    idxBatch += 1
                    continue

            if idxBatch > idxLast + 1:
                # Clusters should not be too big
                batchSeq = BatchLetSequence(self.m_listBatchLets[idxLast: idxBatch], "Args")
                self.m_listBatchLets[idxLast: idxBatch] = [batchSeq]

                lenBatch -= (idxBatch - idxLast - 1)
                numSubst += 1

            idxLast += 1
            idxBatch = idxLast + 1
        return numSubst

    def __dump_flow_internal(self, batchDump):
        batchDump.flow_header()
        for aBtch in self.m_listBatchLets:
            batchDump.dump_batch_to_stream(aBtch)
        batchDump.flow_footer()

    def __dump_flow_simple(self, strm, batchConstructor):
        batchDump = batchConstructor(strm)
        self.__dump_flow_internal(batchDump)

    def dump_flow_constructor(self, batchDump, flow_process_id=None):
        self.__dump_flow_internal(batchDump)

    def factorise_one_flow(self, verbose, batchConstructor):

        if verbose > 1: self.__dump_flow_simple(sys.stdout, batchConstructor)

        if verbose > 0:
            sys.stdout.write("\n")
            sys.stdout.write("factorise_one_flow lenBatch=%d\n" % (len(self.m_listBatchLets)))
        numSubst = self.__filter_matched_batches()
        if verbose > 0:
            sys.stdout.write("factorise_one_flow numSubst=%d lenBatch=%d\n" % (numSubst, len(self.m_listBatchLets)))

        idxLoops = 0
        while True:
            if verbose > 1:
                self.__dump_flow_simple(sys.stdout, batchConstructor)

            if verbose > 0:
                sys.stdout.write("\n")
                sys.stdout.write("factorise_one_flow lenBatch=%d\n" % (len(self.m_listBatchLets)))
            numSubst = self.__clusterize_bigrams()
            if verbose > 0:
                sys.stdout.write("factorise_one_flow numSubst=%d lenBatch=%d\n" % (numSubst, len(self.m_listBatchLets)))
            if numSubst == 0:
                break
            idxLoops += 1

        if verbose > 1: self.__dump_flow_simple(sys.stdout, batchConstructor)

        if verbose > 0:
            sys.stdout.write("\n")
            sys.stdout.write("factorise_one_flow lenBatch=%d\n" % (len(self.m_listBatchLets)))
        numSubst = self.__clusterize_batches_by_arguments()
        if verbose > 0:
            sys.stdout.write(
                "factorise_one_flow numSubst=%d lenBatch=%d\n" % (numSubst, len(self.m_listBatchLets)))

        if verbose > 1: self.__dump_flow_simple(sys.stdout, batchConstructor)

